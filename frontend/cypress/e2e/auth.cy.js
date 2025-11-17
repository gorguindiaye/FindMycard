describe('Authentication', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('should load the home page', () => {
    cy.contains('FindMyID').should('be.visible')
  })

  it('should navigate to login page', () => {
    cy.contains('Connexion').click()
    cy.url().should('include', '/auth')
    cy.contains('Se connecter').should('be.visible')
  })

  it('should navigate to register page', () => {
    cy.contains('Inscription').click()
    cy.url().should('include', '/auth')
    cy.contains('Créer un compte').should('be.visible')
  })

  it('should show validation errors on empty form submission', () => {
    cy.contains('Connexion').click()
    cy.get('button[type="submit"]').click()
    // Check for validation messages
    cy.contains('requis').should('be.visible')
  })

  it('should register a new user', () => {
    cy.contains('Inscription').click()

    const timestamp = Date.now()
    const email = `test${timestamp}@example.com`

    cy.get('input[name="email"]').type(email)
    cy.get('input[name="first_name"]').type('Test')
    cy.get('input[name="last_name"]').type('User')
    cy.get('input[name="password"]').type('testpass123')
    cy.get('input[name="password_confirm"]').type('testpass123')

    cy.get('button[type="submit"]').click()

    // Should redirect to login or dashboard
    cy.url().should('not.include', '/auth')
  })
})
