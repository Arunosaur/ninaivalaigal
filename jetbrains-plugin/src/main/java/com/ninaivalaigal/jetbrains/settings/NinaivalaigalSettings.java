package com.ninaivalaigal.jetbrains.settings;

import com.intellij.openapi.application.ApplicationManager;
import com.intellij.openapi.components.PersistentStateComponent;
import com.intellij.openapi.components.State;
import com.intellij.openapi.components.Storage;
import com.intellij.util.xmlb.XmlSerializerUtil;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * Ninaivalaigal Plugin Settings
 * Persists configuration for ninaivalaigal MCP server connection
 */
@State(
    name = "com.ninaivalaigal.jetbrains.settings.NinaivalaigalSettings",
    storages = @Storage("NinaivalaigalSettings.xml")
)
public class NinaivalaigalSettings implements PersistentStateComponent<NinaivalaigalSettings> {
    // MCP server path (path to ninaivalaigal MCP server script)
    public String mcpServerPath = "";

    // Default context name (if auto-detect disabled)
    public String defaultContext = "";

    // Auto-detect context from project folder name
    public boolean autoDetectContext = true;

    public static NinaivalaigalSettings getInstance() {
        return ApplicationManager.getApplication().getService(NinaivalaigalSettings.class);
    }

    @Nullable
    @Override
    public NinaivalaigalSettings getState() {
        return this;
    }

    @Override
    public void loadState(@NotNull NinaivalaigalSettings state) {
        XmlSerializerUtil.copyBean(state, this);
    }

    public String getMcpServerPath() {
        return mcpServerPath;
    }

    public void setMcpServerPath(String mcpServerPath) {
        this.mcpServerPath = mcpServerPath;
    }

    public String getDefaultContext() {
        return defaultContext;
    }

    public void setDefaultContext(String defaultContext) {
        this.defaultContext = defaultContext;
    }

    public boolean isAutoDetectContext() {
        return autoDetectContext;
    }

    public void setAutoDetectContext(boolean autoDetectContext) {
        this.autoDetectContext = autoDetectContext;
    }
}
