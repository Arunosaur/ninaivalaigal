package com.mem0.jetbrains.actions;

import com.intellij.openapi.actionSystem.AnAction;
import com.intellij.openapi.actionSystem.AnActionEvent;
import com.intellij.openapi.actionSystem.CommonDataKeys;
import com.intellij.openapi.editor.Editor;
import com.intellij.openapi.editor.SelectionModel;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.ui.Messages;
import com.mem0.jetbrains.Mem0Client;
import org.jetbrains.annotations.NotNull;

public class RememberAction extends AnAction {

    @Override
    public void actionPerformed(@NotNull AnActionEvent e) {
        Project project = e.getProject();
        Editor editor = e.getData(CommonDataKeys.EDITOR);
        
        if (project == null) {
            Messages.showErrorDialog("No project found", "mem0 Error");
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
                "mem0 - Remember",
                Messages.getQuestionIcon()
            );
        }
        
        if (textToRemember != null && !textToRemember.trim().isEmpty()) {
            Mem0Client client = new Mem0Client(project);
            
            if (!client.isServerRunning()) {
                Messages.showErrorDialog(
                    "mem0 server is not running. Please start it with: ./manage.sh start",
                    "mem0 Server Error"
                );
                return;
            }
            
            boolean success = client.remember(textToRemember.trim());
            
            if (success) {
                Messages.showInfoMessage(
                    "Memory saved to context: " + client.getCurrentContext(),
                    "mem0 - Success"
                );
            } else {
                Messages.showErrorDialog(
                    "Failed to save memory. Check mem0 server connection.",
                    "mem0 Error"
                );
            }
        }
    }
}
