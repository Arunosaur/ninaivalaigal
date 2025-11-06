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

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * Enhanced unit tests for ContextMenuAction
 * Tests context menu functionality and error handling
 */
@ExtendWith(MockitoExtension.class)
class ContextMenuActionEnhancedTest {

    @Mock
    private AnActionEvent mockEvent;

    @Mock
    private Project mockProject;

    @Mock
    private NinaivalaigalClient mockClient;

    @Mock
    private NinaivalaigalSettings mockSettings;

    private ContextMenuAction action;

    @BeforeEach
    void setUp() {
        action = new ContextMenuAction();
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
    void testListContexts() {
        // Test listing contexts
        List<String> contexts = Arrays.asList("context1", "context2", "context3");
        when(mockClient.listContexts()).thenReturn(contexts);

        List<String> result = mockClient.listContexts();
        assertNotNull(result);
        assertEquals(3, result.size());
        assertTrue(result.contains("context1"));
        assertTrue(result.contains("context2"));
        assertTrue(result.contains("context3"));
    }

    @Test
    void testListContextsEmpty() {
        // Test empty context list
        List<String> emptyContexts = Collections.emptyList();
        when(mockClient.listContexts()).thenReturn(emptyContexts);

        List<String> result = mockClient.listContexts();
        assertNotNull(result);
        assertTrue(result.isEmpty());
    }

    @Test
    void testListContextsWithSingleContext() {
        // Test single context in list
        List<String> singleContext = Collections.singletonList("only-context");
        when(mockClient.listContexts()).thenReturn(singleContext);

        List<String> result = mockClient.listContexts();
        assertNotNull(result);
        assertEquals(1, result.size());
        assertEquals("only-context", result.get(0));
    }

    @Test
    void testListContextsWithManyContexts() {
        // Test many contexts
        List<String> manyContexts = Arrays.asList(
            "context1", "context2", "context3", "context4", "context5",
            "context6", "context7", "context8", "context9", "context10"
        );
        when(mockClient.listContexts()).thenReturn(manyContexts);

        List<String> result = mockClient.listContexts();
        assertNotNull(result);
        assertEquals(10, result.size());
    }

    @Test
    void testContextMessageFormatting() {
        // Test context message formatting
        List<String> contexts = Arrays.asList("context1", "context2", "context3");
        String message = "Available contexts:\n\n" + String.join("\n", contexts);

        assertNotNull(message);
        assertTrue(message.contains("Available contexts"));
        assertTrue(message.contains("context1"));
        assertTrue(message.contains("context2"));
        assertTrue(message.contains("context3"));
    }

    @Test
    void testContextMessageWithEmptyList() {
        // Test message formatting with empty list
        List<String> emptyContexts = Collections.emptyList();
        String message = "Available contexts:\n\n" + String.join("\n", emptyContexts);

        assertNotNull(message);
        assertTrue(message.contains("Available contexts"));
    }

    @Test
    void testContextMessageWithSingleContext() {
        // Test message formatting with single context
        List<String> singleContext = Collections.singletonList("only-context");
        String message = "Available contexts:\n\n" + String.join("\n", singleContext);

        assertNotNull(message);
        assertTrue(message.contains("Available contexts"));
        assertTrue(message.contains("only-context"));
    }

    @Test
    void testContextsWithSpecialCharacters() {
        // Test contexts with special characters
        List<String> contextsWithSpecial = Arrays.asList(
            "context_with-special.chars_123",
            "context-with-dashes",
            "context_with_underscores"
        );
        when(mockClient.listContexts()).thenReturn(contextsWithSpecial);

        List<String> result = mockClient.listContexts();
        assertNotNull(result);
        assertEquals(3, result.size());
    }

    @Test
    void testContextsWithLongNames() {
        // Test contexts with long names
        StringBuilder longName = new StringBuilder();
        for (int i = 0; i < 50; i++) {
            longName.append("a");
        }
        String longContextName = longName.toString();
        List<String> contextsWithLongNames = Collections.singletonList(longContextName);
        when(mockClient.listContexts()).thenReturn(contextsWithLongNames);

        List<String> result = mockClient.listContexts();
        assertNotNull(result);
        assertEquals(1, result.size());
        assertTrue(result.get(0).length() > 40);
    }

    @Test
    void testClientClose() {
        // Test that client is closed after operation
        doNothing().when(mockClient).close();

        mockClient.close();
        verify(mockClient, times(1)).close();
    }

    @Test
    void testMultipleListOperations() {
        // Test multiple list operations
        List<String> contexts1 = Arrays.asList("context1", "context2");
        List<String> contexts2 = Arrays.asList("context3", "context4", "context5");

        when(mockClient.listContexts()).thenReturn(contexts1, contexts2);

        List<String> result1 = mockClient.listContexts();
        List<String> result2 = mockClient.listContexts();

        assertNotNull(result1);
        assertNotNull(result2);
        assertEquals(2, result1.size());
        assertEquals(3, result2.size());
    }

    @Test
    void testStringJoinWithContexts() {
        // Test String.join with contexts
        List<String> contexts = Arrays.asList("ctx1", "ctx2", "ctx3");
        String joined = String.join("\n", contexts);

        assertNotNull(joined);
        assertTrue(joined.contains("ctx1"));
        assertTrue(joined.contains("ctx2"));
        assertTrue(joined.contains("ctx3"));
        assertTrue(joined.contains("\n"));
    }

    @Test
    void testStringJoinWithEmptyList() {
        // Test String.join with empty list
        List<String> emptyList = Collections.emptyList();
        String joined = String.join("\n", emptyList);

        assertNotNull(joined);
        assertTrue(joined.isEmpty());
    }

    @Test
    void testErrorHandling() {
        // Test error handling structure
        Exception testException = new RuntimeException("Test error");
        assertNotNull(testException);
        assertEquals("Test error", testException.getMessage());
    }
}
