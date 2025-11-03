package com.ninaivalaigal.jetbrains.actions;

import com.intellij.openapi.actionSystem.AnAction;
import com.intellij.openapi.actionSystem.AnActionEvent;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.ui.Messages;
import com.ninaivalaigal.jetbrains.NinaivalaigalClient;
import com.ninaivalaigal.jetbrains.settings.NinaivalaigalSettings;
import org.jetbrains.annotations.NotNull;

import java.util.List;

/**
 * Action to manage ninaivalaigal contexts
 */
public class ContextMenuAction extends AnAction {

    @Override
    public void actionPerformed(@NotNull AnActionEvent e) {
        Project project = e.getProject();

        if (project == null) {
            Messages.showErrorDialog("No project found", "Ninaivalaigal Error");
            return;
        }

        NinaivalaigalSettings settings = NinaivalaigalSettings.getInstance();
        NinaivalaigalClient client = new NinaivalaigalClient(project, settings);

        if (!client.isServerRunning()) {
            Messages.showErrorDialog(
                "Ninaivalaigal MCP server is not running. Please check your MCP server path in settings.",
                "Ninaivalaigal Server Error"
            );
            return;
        }

        List<String> contexts = client.listContexts();
        String message = "Available contexts:\n\n" + String.join("\n", contexts);
        Messages.showInfoDialog(
            project,
            message,
            "Ninaivalaigal - Contexts"
        );

        client.close();
    }
}
