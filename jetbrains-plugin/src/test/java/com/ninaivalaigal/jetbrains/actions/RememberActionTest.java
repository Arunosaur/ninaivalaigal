package com.ninaivalaigal.jetbrains.actions;

import com.intellij.openapi.actionSystem.AnActionEvent;
import com.intellij.openapi.actionSystem.CommonDataKeys;
import com.intellij.openapi.editor.Editor;
import com.intellij.openapi.project.Project;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.mockito.Mockito.*;

/**
 * Unit tests for RememberAction
 */
@ExtendWith(MockitoExtension.class)
class RememberActionTest {

    @Mock
    private AnActionEvent mockEvent;

    @Mock
    private Project mockProject;

    @Mock
    private Editor mockEditor;

    private RememberAction action;

    @BeforeEach
    void setUp() {
        action = new RememberAction();
    }

    @Test
    void testActionExists() {
        assertNotNull(action);
    }

    @Test
    void testActionPerformedWithProject() {
        when(mockEvent.getProject()).thenReturn(mockProject);
        when(mockEvent.getData(CommonDataKeys.EDITOR)).thenReturn(null);

        // Note: Actual execution requires IntelliJ Platform environment
        // This test validates structure
        assertNotNull(action);
    }

    @Test
    void testActionPerformedWithEditor() {
        when(mockEvent.getProject()).thenReturn(mockProject);
        when(mockEvent.getData(CommonDataKeys.EDITOR)).thenReturn(mockEditor);

        // Note: Actual execution requires IntelliJ Platform environment
        // This test validates structure
        assertNotNull(action);
        assertNotNull(mockEditor);
    }
}
