Feature: Gateway API Hello World
  As an API consumer
  I want to interact with the Gateway API
  So that I can verify it responds correctly to valid and invalid requests

  Background: The API is running
    Given the API is running

  Scenario: Get structured record request
    When I send a valid Parameters resource to the endpoint
    Then the response status code should be 200
    And the response should contain the patient bundle from the provider

  Scenario: Accessing a non-existent endpoint returns a 404
    When I send a valid Parameters resource to a nonexistent endpoint
    Then the response status code should be 404
