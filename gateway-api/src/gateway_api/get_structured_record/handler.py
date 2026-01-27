from gateway_api.controller import Controller
from gateway_api.get_structured_record.request import GetStructuredRecordRequest


class GetStructuredRecordHandler:
    @classmethod
    def handle(cls, request: GetStructuredRecordRequest) -> None:
        try:
            controller = Controller()
        except Exception as e:
            request.set_negative_response(f"Failed to initialize controller: {e}")
            return

        flask_response = controller.run(request=request)

        request.set_response_from_flaskresponse(flask_response)
