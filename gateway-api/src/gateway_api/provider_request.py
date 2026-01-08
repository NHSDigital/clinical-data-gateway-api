"""
Module: gateway_api.provider_request

This module contains the GPProvider class, which provides a
simple client for GPProvider FHIR GP System.
The GPProvider class has a sigle method to get_structure_record which
can be used to fetch patient records from a GPProvider FHIR API endpoint.
Usage:

    instantiate a GPProvider with:
            provider_endpoint
            provider_ASID
            consumer_ASID

    method get_structured_record with (may add optional parameters later):
        Parameters: parameters resource

    returns the response from the provider FHIR API.

"""
