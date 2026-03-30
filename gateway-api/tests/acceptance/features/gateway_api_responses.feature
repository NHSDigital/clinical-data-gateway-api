Feature: Gateway API Response Behaviour
  As an API consumer
  I want to interact with the Gateway API
  So that I can verify it responds correctly to valid and invalid requests

  Background: The API is running
    Given the API is running

  Scenario: Valid structured record request returns the expected patient record
    When I send a valid Parameters resource to the endpoint
    Then the response should be successful
    And the response should include the patient's record from the provider

  Scenario: Valid structured record request to a non-existent endpoint returns an endpoint not found error
    When I send a valid Parameters resource to a nonexistent endpoint
    Then the response should indicate the endpoint was not found
