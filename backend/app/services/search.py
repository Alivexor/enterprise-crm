from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.search import SearchRepository
from app.schemas.search import SearchEntityType, SearchResponse, SearchResult


class SearchService:
    def __init__(self, search_repository: SearchRepository) -> None:
        self.search_repository = search_repository

    def search(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        query: str,
        limit_per_type: int,
        allowed_entity_types: frozenset[SearchEntityType],
    ) -> SearchResponse:
        companies = (
            self.search_repository.search_companies(
                database_session, organization_id, query, limit_per_type
            )
            if "company" in allowed_entity_types
            else []
        )
        contacts = (
            self.search_repository.search_contacts(
                database_session, organization_id, query, limit_per_type
            )
            if "contact" in allowed_entity_types
            else []
        )
        leads = (
            self.search_repository.search_leads(
                database_session, organization_id, query, limit_per_type
            )
            if "lead" in allowed_entity_types
            else []
        )
        deals = (
            self.search_repository.search_deals(
                database_session, organization_id, query, limit_per_type
            )
            if "deal" in allowed_entity_types
            else []
        )
        tasks = (
            self.search_repository.search_tasks(
                database_session, organization_id, query, limit_per_type
            )
            if "task" in allowed_entity_types
            else []
        )
        activities = (
            self.search_repository.search_activities(
                database_session, organization_id, query, limit_per_type
            )
            if "activity" in allowed_entity_types
            else []
        )
        notes = (
            self.search_repository.search_notes(
                database_session, organization_id, query, limit_per_type
            )
            if "note" in allowed_entity_types
            else []
        )
        return SearchResponse(
            items=[
                *(
                    SearchResult(
                        entity_type="company",
                        id=company.id,
                        title=company.name,
                        subtitle=company.industry,
                    )
                    for company in companies
                ),
                *(
                    SearchResult(
                        entity_type="contact",
                        id=contact.id,
                        title=f"{contact.first_name} {contact.last_name}",
                        subtitle=contact.email,
                    )
                    for contact in contacts
                ),
                *(
                    SearchResult(
                        entity_type="lead",
                        id=lead.id,
                        title=lead.title,
                        subtitle=lead.status,
                    )
                    for lead in leads
                ),
                *(
                    SearchResult(
                        entity_type="deal",
                        id=deal.id,
                        title=deal.title,
                        subtitle=deal.status,
                    )
                    for deal in deals
                ),
                *(
                    SearchResult(
                        entity_type="task",
                        id=task.id,
                        title=task.title,
                        subtitle=task.status,
                    )
                    for task in tasks
                ),
                *(
                    SearchResult(
                        entity_type="activity",
                        id=activity.id,
                        title=activity.title,
                        subtitle=activity.type,
                    )
                    for activity in activities
                ),
                *(
                    SearchResult(
                        entity_type="note",
                        id=note.id,
                        title="Note",
                        subtitle=note.content[:120],
                    )
                    for note in notes
                ),
            ]
        )


search_service = SearchService(SearchRepository())
