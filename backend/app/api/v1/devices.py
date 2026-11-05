from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import ErrorResponse
from app.schemas.device import DeviceRegister, DeviceUnregister
from app.services import device_service

router = APIRouter(
    prefix="/devices",
    tags=["devices"],
    responses={401: {"model": ErrorResponse, "description": "Missing or invalid token"}},
)


@router.post("", status_code=status.HTTP_204_NO_CONTENT, summary="Save this phone's push token")
def register_device(body: DeviceRegister, current_user: CurrentUser, db: DbSession) -> None:
    device_service.register(db, current_user.id, body.token, body.platform)


@router.post("/unregister", status_code=status.HTTP_204_NO_CONTENT, summary="Stop pushes to this phone")
def unregister_device(body: DeviceUnregister, current_user: CurrentUser, db: DbSession) -> None:
    device_service.unregister(db, current_user.id, body.token)
