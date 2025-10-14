// E2E Test Template

describe('Example E2E Test', () => {
  it('should complete a user workflow', () => {
    // Arrange: Visit the initial page
    cy.visit('/');

    // Act: Interact with the UI
    cy.get('input[name="username"]').type('testuser');
    cy.get('input[name="password"]').type('password');
    cy.get('button[type="submit"]').click();

    // Assert: Verify the outcome
    cy.url().should('include', '/dashboard');
    cy.contains('Welcome, testuser');
  });
});
