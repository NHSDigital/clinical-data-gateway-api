Feature: Gateway API Hello World
  As an API consumer
  I want to interact with the Gateway API
  So that I can verify it responds correctly to valid and invalid requests

  Background: The API is running
    Given the API is running

  Scenario: Get hello world message
    When I send a GET request to "/"
    Then the response status code should be 200
    And the response should contain "Hello, World!"

  Scenario: Accessing a non-existent endpoint returns a 404
    When I send a GET request to "/nonexistent"
    Then the response status code should be 404
