from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.demo_seed import DemoDataService


def main() -> None:
    with SessionLocal() as session:
        result = DemoDataService(get_settings()).clear(session)
    print(
        "Showcase demo cleanup complete: "
        f"users={result.users}, roles={result.roles}, companies={result.companies}, contacts={result.contacts}, "
        f"leads={result.leads}, pipelines={result.pipelines}, pipeline_stages={result.pipeline_stages}, "
        f"deals={result.deals}, tasks={result.tasks}, activities={result.activities}, notes={result.notes}, "
        f"tags={result.tags}, notifications={result.notifications}, saved_views={result.saved_views}, custom_fields={result.custom_fields}, "
        f"workflows={result.workflows}, goals={result.goals}, products={result.products}, quotes={result.quotes}, "
        f"dashboard_widgets={result.dashboard_widgets}, sequences={result.sequences}, sequence_enrollments={result.sequence_enrollments}"
    )


if __name__ == "__main__":
    main()
