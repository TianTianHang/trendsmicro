import json
from sqlalchemy.orm import Session
from dependencies.database import get_db
from models.permission import Permission

def import_permissions(file_path: str, db: Session):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        service_name = data['service_name']
        permissions = data['permissions']
        for permission in permissions:
            existing_permission = db.query(Permission).filter_by(
                service_name=service_name,
                path=permission['path']
            ).first()
            if not existing_permission:
                route_permission = Permission(
                    service_name=service_name,
                    path=permission['path'],
                    required_permission=','.join(permission['required_permission'])
                )
                db.add(route_permission)
        db.commit()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python import_permissions.py <path_to_permissions_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    db = next(get_db())
    import_permissions(file_path, db)
