package com.ninaivalaigal.jetbrains.actions;

import com.intellij.openapi.actionSystem.AnAction;
import com.intellij.openapi.actionSystem.AnActionEvent;
import com.intellij.openapi.actionSystem.CommonDataKeys;
import com.intellij.openapi.editor.Editor;
import com.intellij.openapi.editor.SelectionModel;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.ui.Messages;
import com.ninaivalaigal.jetbrains.NinaivalaigalClient;
import com.ninaivalaigal.jetbrains.settings.NinaivalaigalSettings;
import org.jetbrains.annotations.NotNull;

/**
 * Action to remember selected text or user input to ninaivalaigal
 */
public class RememberAction extends AnAction {

    @Override
    public void actionPerformed(@NotNull AnActionEvent e) {
        Project project = e.getProject();
        Editor editor = e.getData(CommonDataKeys.EDITOR);

        if (project == null) {
            Messages.showErrorDialog("No project found", "Ninaivalaigal Error");
            return;
        }

        String textToRemember = "";

        if (editor != null) {
            SelectionModel selectionModel = editor.getSelectionModel();
            if (selectionModel.hasSelection()) {
                textToRemember = selectionModel.getSelectedText();
            }
        }

        if (textToRemember.isEmpty()) {
            textToRemember = Messages.showInputDialog(
                project,
                "Enter text to remember:",
                "Ninaivalaigal - Remember",
                Messages.getQuestionIcon()
            );
        }

        if (textToRemember != null && !textToRemember.trim().isEmpty()) {
            NinaivalaigalSettings settings = NinaivalaigalSettings.getInstance();
            NinaivalaigalClient client = new NinaivalaigalClient(project, settings);

            if (!client.isServerRunning()) {
                Messages.showErrorDialog(
                    "Ninaivalaigal MCP server is not running. Please check your MCP server path in settings.",
                    "Ninaivalaigal Server Error"
                );
                return;
            }

            boolean success = client.remember(textToRemember.trim());

            if (success) {
                Messages.showInfoMessage(
                    "Memory saved to context: " + client.getCurrentContext(),
                    "Ninaivalaigal - Success"
                );
            } else {
                Messages.showErrorDialog(
                    "Failed to save memory. Check ninaivalaigal MCP server connection.",
                    "Ninaivalaigal Error"
                );
            }

            client.close();
        }
    }
}
