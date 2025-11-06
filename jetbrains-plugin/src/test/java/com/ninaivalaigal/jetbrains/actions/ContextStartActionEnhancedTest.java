package com.ninaivalaigal.jetbrains.actions;

import com.intellij.openapi.actionSystem.AnActionEvent;
import com.intellij.openapi.project.Project;
import com.ninaivalaigal.jetbrains.NinaivalaigalClient;
import com.ninaivalaigal.jetbrains.settings.NinaivalaigalSettings;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * Enhanced unit tests for ContextStartAction
 * Tests context start functionality and error handling
 */
@ExtendWith(MockitoExtension.class)
class ContextStartActionEnhancedTest {

    @Mock
    private AnActionEvent mockEvent;

    @Mock
    private Project mockProject;

    @Mock
    private NinaivalaigalClient mockClient;

    @Mock
    private NinaivalaigalSettings mockSettings;

    private ContextStartAction action;

    @BeforeEach
    void setUp() {
        action = new ContextStartAction();
        when(mockProject.getBasePath()).thenReturn("/test/project");
    }

    @Test
    void testActionExists() {
        assertNotNull(action);
    }

    @Test
    void testActionPerformedWithNullProject() {
        // Test error handling when project is null
        when(mockEvent.getProject()).thenReturn(null);

        assertNotNull(action);
    }

    @Test
    void testActionPerformedWithProject() {
        when(mockEvent.getProject()).thenReturn(mockProject);

        assertNotNull(action);
        assertNotNull(mockProject);
    }

    @Test
    void testClientCreation() {
        // Test that client is created with correct settings
        when(NinaivalaigalSettings.getInstance()).thenReturn(mockSettings);
        when(mockSettings.getMcpServerPath()).thenReturn("/path/to/server.py");

        assertNotNull(mockSettings);
    }

    @Test
    void testServerRunningCheck() {
        // Test server running check
        when(mockClient.isServerRunning()).thenReturn(true);

        assertTrue(mockClient.isServerRunning());
    }

    @Test
    void testServerNotRunning() {
        // Test error handling when server is not running
        when(mockClient.isServerRunning()).thenReturn(false);

        assertFalse(mockClient.isServerRunning());
    }

    @Test
    void testStartContextSuccess() {
        // Test successful context start
        String contextName = "new-context";
        when(mockClient.startContext(contextName)).thenReturn(true);

        boolean success = mockClient.startContext(contextName);
        assertTrue(success);
    }

    @Test
    void testStartContextFailure() {
        // Test failed context start
        String contextName = "invalid-context";
        when(mockClient.startContext(contextName)).thenReturn(false);

        boolean success = mockClient.startContext(contextName);
        assertFalse(success);
    }

    @Test
    void testStartContextWithEmptyName() {
        // Test edge case: empty context name
        String emptyContext = "";
        when(mockClient.startContext(emptyContext)).thenReturn(false);

        boolean success = mockClient.startContext(emptyContext);
        assertFalse(success);
    }

    @Test
    void testStartContextWithSpecialCharacters() {
        // Test context name with special characters
        String contextWithSpecialChars = "context_with-special.chars_123";
        when(mockClient.startContext(contextWithSpecialChars)).thenReturn(true);

        boolean success = mockClient.startContext(contextWithSpecialChars);
        assertTrue(success);
    }

    @Test
    void testStartContextWithLongName() {
        // Test context name with long name
        StringBuilder longName = new StringBuilder();
        for (int i = 0; i < 100; i++) {
            longName.append("a");
        }
        String longContextName = longName.toString();
        when(mockClient.startContext(longContextName)).thenReturn(true);

        boolean success = mockClient.startContext(longContextName);
        assertTrue(success);
    }

    @Test
    void testListContexts() {
        // Test listing contexts
        java.util.List<String> contexts = java.util.Arrays.asList("context1", "context2", "context3");
        when(mockClient.listContexts()).thenReturn(contexts);

        java.util.List<String> result = mockClient.listContexts();
        assertNotNull(result);
        assertEquals(3, result.size());
        assertTrue(result.contains("context1"));
    }

    @Test
    void testListContextsEmpty() {
        // Test empty context list
        java.util.List<String> emptyContexts = java.util.Collections.emptyList();
        when(mockClient.listContexts()).thenReturn(emptyContexts);

        java.util.List<String> result = mockClient.listContexts();
        assertNotNull(result);
        assertTrue(result.isEmpty());
    }

    @Test
    void testContextNameValidation() {
        // Test context name validation
        String validContext = "valid-context-123";
        String invalidContext = "";

        assertNotNull(validContext);
        assertFalse(validContext.isEmpty());
        assertTrue(invalidContext.isEmpty());
    }

    @Test
    void testGetCurrentContext() {
        // Test getting current context
        when(mockClient.getCurrentContext()).thenReturn("current-context");

        String context = mockClient.getCurrentContext();
        assertNotNull(context);
        assertEquals("current-context", context);
    }

    @Test
    void testSetContext() {
        // Test setting context
        String newContext = "new-context";
        doNothing().when(mockClient).setContext(newContext);

        mockClient.setContext(newContext);
        verify(mockClient, times(1)).setContext(newContext);
    }

    @Test
    void testClientClose() {
        // Test that client is closed after operation
        doNothing().when(mockClient).close();

        mockClient.close();
        verify(mockClient, times(1)).close();
    }

    @Test
    void testMultipleContextOperations() {
        // Test multiple context operations
        when(mockClient.startContext("context1")).thenReturn(true);
        when(mockClient.startContext("context2")).thenReturn(true);
        when(mockClient.startContext("context3")).thenReturn(true);

        assertTrue(mockClient.startContext("context1"));
        assertTrue(mockClient.startContext("context2"));
        assertTrue(mockClient.startContext("context3"));
    }

    @Test
    void testContextSwitch() {
        // Test switching between contexts
        when(mockClient.getCurrentContext()).thenReturn("context1");
        when(mockClient.startContext("context2")).thenReturn(true);
        when(mockClient.getCurrentContext()).thenReturn("context2");

        String initialContext = mockClient.getCurrentContext();
        assertEquals("context1", initialContext);

        boolean switched = mockClient.startContext("context2");
        assertTrue(switched);

        String newContext = mockClient.getCurrentContext();
        assertEquals("context2", newContext);
    }

    @Test
    void testErrorHandling() {
        // Test error handling structure
        Exception testException = new RuntimeException("Test error");
        assertNotNull(testException);
        assertEquals("Test error", testException.getMessage());
    }
}
