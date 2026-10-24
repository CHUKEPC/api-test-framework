"""Scaffold template for new YAML test suites."""

INIT_YAML_TEMPLATE = """# API Test Suite Specification
name: "User Management API Tests"
description: "Demonstrates request chaining, variable extraction, and assertions"
base_url: "https://jsonplaceholder.typicode.com"

# Shared headers applied to all requests in this suite
headers:
  Content-Type: "application/json"
  Accept: "application/json"

# Initial suite variables (supports Jinja2 expressions like {{ uuid() }})
variables:
  sample_title: "PetProject Automated Test"
  sample_body: "Created by api-test-framework"

# Lifecycle hooks
hooks:
  setup: []
  teardown: []

# Ordered list of test cases
tests:
  - name: "Create new post"
    description: "POST request creating a post and extracting its generated ID"
    request:
      method: "POST"
      url: "/posts"
      json:
        title: "{{ sample_title }}"
        body: "{{ sample_body }}"
        userId: 1
    assertions:
      status_code: 201
      headers:
        content-type:
          op: "contains"
          expected: "application/json"
      jsonpath:
        - path: "$.id"
          op: "exists"
        - path: "$.title"
          op: "equals"
          expected: "{{ sample_title }}"
      max_duration: 3.0
    extract:
      - name: "created_post_id"
        source: "jsonpath"
        expression: "$.id"

  - name: "Get created post by ID"
    description: "GET request using the extracted post ID from previous test"
    request:
      method: "GET"
      url: "/posts/1" # JSONPlaceholder simulates post 1
      query_params:
        client: "api-test-framework"
    assertions:
      status_code: 200
      jsonpath:
        - path: "$.id"
          op: "equals"
          expected: 1
        - path: "$.userId"
          op: "type"
          expected: "int"
      max_duration: 2.0

  - name: "Update post"
    description: "PUT request updating post content"
    request:
      method: "PUT"
      url: "/posts/1"
      json:
        id: 1
        title: "Updated Title"
        body: "Updated Body"
        userId: 1
    assertions:
      status_code: 200
      jsonpath:
        - path: "$.title"
          op: "equals"
          expected: "Updated Title"

  - name: "Delete post"
    description: "DELETE request verifying successful deletion"
    request:
      method: "DELETE"
      url: "/posts/1"
    assertions:
      status_code: 200
"""
