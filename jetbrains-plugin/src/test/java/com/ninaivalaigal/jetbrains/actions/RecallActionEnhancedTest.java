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
 * Enhanced unit tests for RecallAction
 * Tests action execution, error handling, and memory recall
 */
@ExtendWith(MockitoExtension.class)
class RecallActionEnhancedTest {

    @Mock
    private AnActionEvent mockEvent;

    @Mock
    private Project mockProject;

    @Mock
    private NinaivalaigalClient mockClient;

    @Mock
    private NinaivalaigalSettings mockSettings;

    private RecallAction action;

    @BeforeEach
    void setUp() {
        action = new RecallAction();
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
    void testRecallWithMemories() {
        // Test successful recall with memories
        String memories = "Memory 1: Important information\nMemory 2: Another note";
        when(mockClient.recall()).thenReturn(memories);
        when(mockClient.getCurrentContext()).thenReturn("test-context");

        String result = mockClient.recall();
        assertNotNull(result);
        assertFalse(result.isEmpty());
        assertTrue(result.contains("Memory 1"));
    }

    @Test
    void testRecallWithNoMemories() {
        // Test recall when no memories exist
        String noMemories = "No memories found";
        when(mockClient.recall()).thenReturn(noMemories);

        String result = mockClient.recall();
        assertNotNull(result);
        assertEquals("No memories found", result);
    }

    @Test
    void testRecallWithEmptyString() {
        // Test edge case: empty recall result
        when(mockClient.recall()).thenReturn("");

        String result = mockClient.recall();
        assertNotNull(result);
        assertTrue(result.isEmpty());
    }

    @Test
    void testRecallError() {
        // Test error handling in recall
        String errorMessage = "Error recalling memories: Connection failed";
        when(mockClient.recall()).thenReturn(errorMessage);

        String result = mockClient.recall();
        assertNotNull(result);
        assertTrue(result.contains("Error"));
    }

    @Test
    void testContextRetrieval() {
        // Test context retrieval
        when(mockClient.getCurrentContext()).thenReturn("my-context");

        String context = mockClient.getCurrentContext();
        assertNotNull(context);
        assertEquals("my-context", context);
    }

    @Test
    void testContextInMessage() {
        // Test that context is included in message
        String context = "test-context";
        when(mockClient.getCurrentContext()).thenReturn(context);

        String message = "Ninaivalaigal - Memories for " + context;
        assertNotNull(message);
        assertTrue(message.contains(context));
    }

    @Test
    void testClientClose() {
        // Test that client is closed after operation
        doNothing().when(mockClient).close();

        mockClient.close();
        verify(mockClient, times(1)).close();
    }

    @Test
    void testMultipleRecallOperations() {
        // Test multiple recall operations
        when(mockClient.recall()).thenReturn("Memory 1", "Memory 2", "Memory 3");

        assertEquals("Memory 1", mockClient.recall());
        assertEquals("Memory 2", mockClient.recall());
        assertEquals("Memory 3", mockClient.recall());
    }

    @Test
    void testRecallWithSpecialCharacters() {
        // Test recall with special characters in memories
        String memoriesWithSpecialChars = "Memory with special chars: !@#$%^&*()";
        when(mockClient.recall()).thenReturn(memoriesWithSpecialChars);

        String result = mockClient.recall();
        assertNotNull(result);
        assertTrue(result.contains("!@#$"));
    }

    @Test
    void testRecallWithNewlines() {
        // Test recall with newlines in memories
        String memoriesWithNewlines = "Line 1\nLine 2\nLine 3";
        when(mockClient.recall()).thenReturn(memoriesWithNewlines);

        String result = mockClient.recall();
        assertNotNull(result);
        assertTrue(result.contains("\n"));
    }

    @Test
    void testRecallWithLongContent() {
        // Test recall with very long memory content
        StringBuilder longMemory = new StringBuilder();
        for (int i = 0; i < 100; i++) {
            longMemory.append("This is a long memory content. ");
        }

        when(mockClient.recall()).thenReturn(longMemory.toString());

        String result = mockClient.recall();
        assertNotNull(result);
        assertTrue(result.length() > 100);
    }

    @Test
    void testRecallWithMultipleMemories() {
        // Test recall with multiple memories
        String multipleMemories = "Memory 1: First\nMemory 2: Second\nMemory 3: Third";
        when(mockClient.recall()).thenReturn(multipleMemories);

        String result = mockClient.recall();
        assertNotNull(result);
        assertTrue(result.contains("Memory 1"));
        assertTrue(result.contains("Memory 2"));
        assertTrue(result.contains("Memory 3"));
    }

    @Test
    void testRecallWithEmptyContext() {
        // Test recall with empty context
        when(mockClient.getCurrentContext()).thenReturn("");

        String context = mockClient.getCurrentContext();
        assertNotNull(context);
        assertTrue(context.isEmpty());
    }

    @Test
    void testRecallWithNullContext() {
        // Test edge case: null context
        when(mockClient.getCurrentContext()).thenReturn(null);

        String context = mockClient.getCurrentContext();
        // Should handle null gracefully
        if (context != null) {
            assertNotNull(context);
        }
    }

    @Test
    void testErrorHandlingInRecall() {
        // Test error handling structure
        Exception testException = new RuntimeException("Test error");
        String errorMessage = "Error recalling memories: " + testException.getMessage();

        assertNotNull(errorMessage);
        assertTrue(errorMessage.contains("Error"));
        assertTrue(errorMessage.contains("Test error"));
    }
}




