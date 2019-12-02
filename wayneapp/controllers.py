from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.utils import json
import logging
from wayneapp.services import BusinessEntityManager, SchemaLoader
from wayneapp.validations.validator import JsonSchemaValidator
from wayneapp.constants import StatusConstants, ResponseConstants


class BusinessEntityController(APIView):
    _entity_manager = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._entity_manager = BusinessEntityManager()
        self._logger = logging.getLogger(__name__)
        self._validator = JsonSchemaValidator()

    def post(self, request: Request, type: str, key: str) -> Response:

        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)

        version = body['payload']['version']
        payload = body['payload']

        response_validation = self._validator.validate_schema(payload, type, version)
        if response_validation[ResponseConstants.RESPONSE_KEY][StatusConstants.STATUS] is StatusConstants.STATUS_ERROR:
            return Response(response_validation, status=status.HTTP_400_BAD_REQUEST)

        try:
            created = self._entity_manager.update_or_create(
                type, key, version, payload
            )
            return self.post_response(created)
        except Exception as e:
            return self.handle_exception(e)

    def post_response(self, created):
        if created:
            return self.custom_response("entity created", status.HTTP_201_CREATED)
        return self.custom_response("entity updated", status.HTTP_200_OK)

    def delete(self, request: Request, type: str, key: str) -> Response:
        try:
            self._entity_manager.delete_by_key(
                type, key
            )
            return self.custom_response("entity deleted", status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)

    def handle_exception(self, exception) -> Response:
        self._logger.exception(exception)
        if type(exception) is AttributeError:
            return self.custom_response(str(exception), status.HTTP_400_BAD_REQUEST)
        return self.custom_response(str(exception), status.HTTP_400_BAD_REQUEST)

    def custom_response(self, message: str, status_code: status) -> Response:
        return Response(
            {
                "message": message
            },
            status=status_code
        )


class SchemaEntityController(APIView):
    _schema_loader = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._schema_loader = SchemaLoader()

    def get(self, request: Request, type: str, version: str) -> Response:
        json_data = self._schema_loader.load(type, version)

        return Response(json.loads(json_data), status=status.HTTP_200_OK)
