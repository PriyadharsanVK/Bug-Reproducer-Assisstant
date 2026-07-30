import asyncio
import uuid
import logging
from sqlalchemy.future import select as sa_select
from apps.api.db.session import AsyncSessionLocal
from apps.api.db.models import AnalysisRun, Issue, AnalysisStatusEnum, Report, Clarification
from apps.api.services.model_router import GroqModelRouter
from apps.api.services.extractor import EntityExtractor
from apps.api.services.repro_planner import ReproPlanner
from apps.api.services.test_generator import TestGenerator
from apps.api.services.hypothesis_engine import HypothesisEngine
from apps.api.services.report_composer import ReportComposer
from apps.api.services.confidence import calculate_overall_repro_confidence

logger = logging.getLogger(__name__)

async def _async_run_pipeline(run_id_str: str):
    async with AsyncSessionLocal() as db:
        try:
            run_uuid = uuid.UUID(run_id_str)
        except ValueError:
            logger.error(f"Invalid UUID string: {run_id_str}")
            return

        run = await db.get(AnalysisRun, run_uuid)
        if not run:
            logger.error(f"Run {run_id_str} not found")
            return

        issue = await db.get(Issue, run.issue_id)
        run.status = AnalysisStatusEnum.RUNNING
        await db.commit()

        try:
            router = GroqModelRouter()
            extractor = EntityExtractor(router)
            planner = ReproPlanner(router)
            test_gen = TestGenerator(router)
            hypo_engine = HypothesisEngine(router)

            # Stage 1: Extraction — augment with any previously submitted answers
            answered_result = await db.execute(
                sa_select(Clarification).where(
                    Clarification.run_id == run.id,
                    Clarification.answer.is_not(None)
                )
            )
            prior_answers = answered_result.scalars().all()

            augmented_body = issue.body
            if prior_answers:
                addendum = "\n\n## Clarification Answers Provided:\n"
                for a in prior_answers:
                    # target_field is stored in options[0]["target_field"]; fall back to question_id
                    opts = a.options or []
                    tf = opts[0].get("target_field", a.question_id) if opts else a.question_id
                    addendum += f"- {tf}: {a.answer}\n"
                augmented_body = issue.body + addendum
                logger.info(
                    f"Run {run_id_str}: injecting {len(prior_answers)} prior answers into extraction context."
                )

            entities = await extractor.extract(issue.title, augmented_body, issue.raw_logs or "")
            
            # Stage 2: Unpack tripartition
            unknowns = entities.get("unknowns", [])
            facts = entities.get("facts", {})
            inferred = entities.get("inferred_assumptions", [])

            # Stage 3: Planning & Generation
            repro_steps = await planner.plan(entities, issue.repository_url or "")
            test_artifacts = await test_gen.generate(entities, repro_steps)
            hypotheses = await hypo_engine.analyze(
                entities,
                issue_body=issue.body,
                raw_logs=issue.raw_logs or ""
            )

            # Stage 4 (was 4): Deterministic Confidence Scoring
            overall_conf = calculate_overall_repro_confidence(facts, inferred, unknowns, repro_steps)
            run.overall_confidence = overall_conf

            # Stage 5 (was 7): needs_input Confidence Gate — evaluated BEFORE report composition.
            # If unknowns exist AND confidence is below threshold, short-circuit here:
            # persist clarification questions and return without generating a report.
            if len(unknowns) > 0 and overall_conf < 0.70:
                logger.info(
                    f"Run {run_id_str}: needs_input gate triggered "
                    f"(unknowns={len(unknowns)}, confidence={overall_conf:.2f}). "
                    "Skipping report generation."
                )
                for idx, unknown in enumerate(unknowns):
                    question_text = f"Please provide more information about: {unknown}"
                    clarification = Clarification(
                        run_id=run.id,
                        question_id=f"q_{idx + 1}",
                        question=question_text,
                        # Store target_field in options so GET /clarifications can read it
                        # without string-parsing the question text
                        options=[{"target_field": unknown}]
                    )
                    db.add(clarification)

                run.status = AnalysisStatusEnum.NEEDS_INPUT
                await db.commit()
                return  # ← early exit: no report generated

            # Stage 6 (was 5): Report Composition — only reached when confidence gate passes
            md_report = ReportComposer.compose_markdown(
                run_id=str(run.id),
                issue_title=issue.title,
                overall_confidence=overall_conf,
                facts=facts,
                inferred_assumptions=inferred,
                unknowns=unknowns,
                repro_steps=repro_steps,
                test_artifacts=test_artifacts,
                hypotheses=hypotheses
            )

            report_obj = Report(
                run_id=run.id,
                markdown_content=md_report,
                json_content={
                    "run_id": str(run.id),
                    "overall_confidence": overall_conf,
                    "facts": facts,
                    "inferred_assumptions": inferred,
                    "unknowns": unknowns,
                    "repro_steps": repro_steps,
                    "test_artifacts": test_artifacts,
                    "hypotheses": hypotheses
                },
                qa_checklist=["Environment verified", "Steps tested", "Test skeleton added"]
            )
            db.add(report_obj)

            run.status = AnalysisStatusEnum.COMPLETED
            await db.commit()

        except Exception as e:
            logger.error(f"Analysis pipeline error for run {run_id_str}: {e}")
            run.status = AnalysisStatusEnum.FAILED
            run.error_message = str(e)
            await db.commit()


