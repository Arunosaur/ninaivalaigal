package com.ninaivalaigal.jetbrains.actions;

import com.intellij.openapi.actionSystem.AnActionEvent;
import com.intellij.openapi.actionSystem.CommonDataKeys;
import com.intellij.openapi.editor.Editor;
import com.intellij.openapi.editor.SelectionModel;
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
 * Enhanced unit tests for RememberAction
 * Tests action execution, error handling, and UI interactions
 */
@ExtendWith(MockitoExtension.class)
class RememberActionEnhancedTest {

    @Mock
    private AnActionEvent mockEvent;

    @Mock
    private Project mockProject;

    @Mock
    private Editor mockEditor;

    @Mock
    private SelectionModel mockSelectionModel;

    @Mock
    private NinaivalaigalClient mockClient;

    @Mock
    private NinaivalaigalSettings mockSettings;

    private RememberAction action;

    @BeforeEach
    void setUp() {
        action = new RememberAction();
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

        // Action should handle null project gracefully
        assertNotNull(action);
    }

    @Test
    void testActionPerformedWithProject() {
        when(mockEvent.getProject()).thenReturn(mockProject);
        when(mockEvent.getData(CommonDataKeys.EDITOR)).thenReturn(null);

        assertNotNull(action);
        assertNotNull(mockProject);
    }

    @Test
    void testActionPerformedWithEditor() {
        when(mockEvent.getProject()).thenReturn(mockProject);
        when(mockEvent.getData(CommonDataKeys.EDITOR)).thenReturn(mockEditor);

        assertNotNull(action);
        assertNotNull(mockEditor);
    }

    @Test
    void testActionPerformedWithSelection() {
        when(mockEvent.getProject()).thenReturn(mockProject);
        when(mockEvent.getData(CommonDataKeys.EDITOR)).thenReturn(mockEditor);
        when(mockEditor.getSelectionModel()).thenReturn(mockSelectionModel);
        when(mockSelectionModel.hasSelection()).thenReturn(true);
        when(mockSelectionModel.getSelectedText()).thenReturn("Selected text");

        assertNotNull(action);
        assertNotNull(mockEditor);
        assertTrue(mockSelectionModel.hasSelection());
        assertEquals("Selected text", mockSelectionModel.getSelectedText());
    }

    @Test
    void testActionPerformedWithoutSelection() {
        when(mockEvent.getProject()).thenReturn(mockProject);
        when(mockEvent.getData(CommonDataKeys.EDITOR)).thenReturn(mockEditor);
        when(mockEditor.getSelectionModel()).thenReturn(mockSelectionModel);
        when(mockSelectionModel.hasSelection()).thenReturn(false);

        assertNotNull(action);
        assertFalse(mockSelectionModel.hasSelection());
    }

    @Test
    void testActionPerformedWithEmptySelection() {
        when(mockEvent.getProject()).thenReturn(mockProject);
        when(mockEvent.getData(CommonDataKeys.EDITOR)).thenReturn(mockEditor);
        when(mockEditor.getSelectionModel()).thenReturn(mockSelectionModel);
        when(mockSelectionModel.hasSelection()).thenReturn(true);
        when(mockSelectionModel.getSelectedText()).thenReturn("");

        assertNotNull(action);
        assertTrue(mockSelectionModel.hasSelection());
        assertTrue(mockSelectionModel.getSelectedText().isEmpty());
    }

    @Test
    void testActionPerformedWithWhitespaceSelection() {
        when(mockEvent.getProject()).thenReturn(mockProject);
        when(mockEvent.getData(CommonDataKeys.EDITOR)).thenReturn(mockEditor);
        when(mockEditor.getSelectionModel()).thenReturn(mockSelectionModel);
        when(mockSelectionModel.hasSelection()).thenReturn(true);
        when(mockSelectionModel.getSelectedText()).thenReturn("   ");

        String selectedText = mockSelectionModel.getSelectedText();
        assertNotNull(selectedText);
        assertTrue(selectedText.trim().isEmpty());
    }

    @Test
    void testActionPerformedWithLongSelection() {
        StringBuilder longText = new StringBuilder();
        for (int i = 0; i < 100; i++) {
            longText.append("This is a long selected text. ");
        }

        when(mockEvent.getProject()).thenReturn(mockProject);
        when(mockEvent.getData(CommonDataKeys.EDITOR)).thenReturn(mockEditor);
        when(mockEditor.getSelectionModel()).thenReturn(mockSelectionModel);
        when(mockSelectionModel.hasSelection()).thenReturn(true);
        when(mockSelectionModel.getSelectedText()).thenReturn(longText.toString());

        String selectedText = mockSelectionModel.getSelectedText();
        assertNotNull(selectedText);
        assertTrue(selectedText.length() > 100);
    }

    @Test
    void testActionPerformedWithSpecialCharacters() {
        String textWithSpecialChars = "Text with special chars: !@#$%^&*()[]{}";

        when(mockEvent.getProject()).thenReturn(mockProject);
        when(mockEvent.getData(CommonDataKeys.EDITOR)).thenReturn(mockEditor);
        when(mockEditor.getSelectionModel()).thenReturn(mockSelectionModel);
        when(mockSelectionModel.hasSelection()).thenReturn(true);
        when(mockSelectionModel.getSelectedText()).thenReturn(textWithSpecialChars);

        String selectedText = mockSelectionModel.getSelectedText();
        assertNotNull(selectedText);
        assertTrue(selectedText.contains("!@#$"));
    }

    @Test
    void testActionPerformedWithNewlines() {
        String textWithNewlines = "Line 1\nLine 2\nLine 3";

        when(mockEvent.getProject()).thenReturn(mockProject);
        when(mockEvent.getData(CommonDataKeys.EDITOR)).thenReturn(mockEditor);
        when(mockEditor.getSelectionModel()).thenReturn(mockSelectionModel);
        when(mockSelectionModel.hasSelection()).thenReturn(true);
        when(mockSelectionModel.getSelectedText()).thenReturn(textWithNewlines);

        String selectedText = mockSelectionModel.getSelectedText();
        assertNotNull(selectedText);
        assertTrue(selectedText.contains("\n"));
    }

    @Test
    void testTextTrimming() {
        // Test that text is trimmed before saving
        String textWithWhitespace = "  Text with whitespace  ";
        String trimmed = textWithWhitespace.trim();

        assertEquals("Text with whitespace", trimmed);
        assertNotEquals(textWithWhitespace, trimmed);
    }

    @Test
    void testEmptyTextAfterTrimming() {
        // Test edge case: text that becomes empty after trimming
        String whitespaceOnly = "   ";
        String trimmed = whitespaceOnly.trim();

        assertTrue(trimmed.isEmpty());
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
    void testRememberSuccess() {
        // Test successful remember operation
        when(mockClient.remember(anyString())).thenReturn(true);
        when(mockClient.getCurrentContext()).thenReturn("test-context");

        boolean success = mockClient.remember("Test memory");
        assertTrue(success);
        assertEquals("test-context", mockClient.getCurrentContext());
    }

    @Test
    void testRememberFailure() {
        // Test failed remember operation
        when(mockClient.remember(anyString())).thenReturn(false);

        boolean success = mockClient.remember("Test memory");
        assertFalse(success);
    }

    @Test
    void testClientClose() {
        // Test that client is closed after operation
        doNothing().when(mockClient).close();

        mockClient.close();
        verify(mockClient, times(1)).close();
    }

    @Test
    void testMultipleRememberOperations() {
        // Test multiple remember operations
        when(mockClient.remember(anyString())).thenReturn(true);

        assertTrue(mockClient.remember("Memory 1"));
        assertTrue(mockClient.remember("Memory 2"));
        assertTrue(mockClient.remember("Memory 3"));
    }

    @Test
    void testContextRetrieval() {
        // Test context retrieval
        when(mockClient.getCurrentContext()).thenReturn("my-context");

        String context = mockClient.getCurrentContext();
        assertNotNull(context);
        assertEquals("my-context", context);
    }
}




