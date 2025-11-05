Feature: Gateway API Hello World
  As an API consumer
  I want to get a hello world message
  So that I can verify the API is working

  Scenario: Get hello world message
    Given the API is running
    When I send a GET request to "/"
    Then the response status code should be 200
    And the response should contain "Hello, World!"

  Scenario: Access non-existent endpoint
    Given the API is running
    When I send a GET request to "/nonexistent"
    Then the response status code should be 404
