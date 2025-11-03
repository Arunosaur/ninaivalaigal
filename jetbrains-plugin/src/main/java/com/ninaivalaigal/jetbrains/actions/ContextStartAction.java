package com.ninaivalaigal.jetbrains.actions;

import com.intellij.openapi.actionSystem.AnAction;
import com.intellij.openapi.actionSystem.AnActionEvent;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.ui.Messages;
import com.ninaivalaigal.jetbrains.NinaivalaigalClient;
import com.ninaivalaigal.jetbrains.settings.NinaivalaigalSettings;
import org.jetbrains.annotations.NotNull;

/**
 * Action to start a new ninaivalaigal context
 */
public class ContextStartAction extends AnAction {

    @Override
    public void actionPerformed(@NotNull AnActionEvent e) {
        Project project = e.getProject();

        if (project == null) {
            Messages.showErrorDialog("No project found", "Ninaivalaigal Error");
            return;
        }

        String contextName = Messages.showInputDialog(
            project,
            "Enter context name:",
            "Ninaivalaigal - Start Context",
            Messages.getQuestionIcon(),
            "",
            null
        );

        if (contextName != null && !contextName.trim().isEmpty()) {
            NinaivalaigalSettings settings = NinaivalaigalSettings.getInstance();
            NinaivalaigalClient client = new NinaivalaigalClient(project, settings);

            if (!client.isServerRunning()) {
                Messages.showErrorDialog(
                    "Ninaivalaigal MCP server is not running. Please check your MCP server path in settings.",
                    "Ninaivalaigal Server Error"
                );
                return;
            }

            boolean success = client.startContext(contextName.trim());

            if (success) {
                Messages.showInfoMessage(
                    "Context started: " + contextName,
                    "Ninaivalaigal - Success"
                );
            } else {
                Messages.showErrorDialog(
                    "Failed to start context. Check ninaivalaigal MCP server connection.",
                    "Ninaivalaigal Error"
                );
            }

            client.close();
        }
    }
}
