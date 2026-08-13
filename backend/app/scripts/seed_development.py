from app.core.config import get_settings
from app.db.session import SessionLocal
from app.repositories.organization import OrganizationRepository
from app.repositories.permission import PermissionRepository
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.services.development_seed import DevelopmentSeedService


def main() -> None:
    settings = get_settings()
    seed_service = DevelopmentSeedService(
        settings,
        OrganizationRepository(),
        PermissionRepository(),
        RoleRepository(),
        UserRepository(),
    )

    with SessionLocal() as database_session:
        result = seed_service.seed(database_session)

    print(
        "Development seed complete: "
        f"organization_created={result.organization_created}, "
        f"role_created={result.role_created}, "
        f"permissions_created={result.permissions_created}, "
        f"user_created={result.user_created}, "
        f"role_assigned={result.role_assigned}, "
        f"permissions_assigned={result.permissions_assigned}"
    )


if __name__ == "__main__":
    main()
