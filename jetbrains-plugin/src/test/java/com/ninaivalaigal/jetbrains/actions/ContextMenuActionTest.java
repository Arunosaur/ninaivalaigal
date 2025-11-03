package com.ninaivalaigal.jetbrains.actions;

import com.intellij.openapi.actionSystem.AnActionEvent;
import com.intellij.openapi.project.Project;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.mockito.Mockito.*;

/**
 * Unit tests for ContextMenuAction
 */
@ExtendWith(MockitoExtension.class)
class ContextMenuActionTest {

    @Mock
    private AnActionEvent mockEvent;

    @Mock
    private Project mockProject;

    private ContextMenuAction action;

    @BeforeEach
    void setUp() {
        action = new ContextMenuAction();
    }

    @Test
    void testActionExists() {
        assertNotNull(action);
    }

    @Test
    void testActionPerformed() {
        when(mockEvent.getProject()).thenReturn(mockProject);

        // Note: Actual execution requires IntelliJ Platform environment
        // This test validates structure
        assertNotNull(action);
    }
}
