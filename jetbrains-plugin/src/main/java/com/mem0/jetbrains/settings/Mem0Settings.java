package com.mem0.jetbrains.settings;

import com.intellij.openapi.application.ApplicationManager;
import com.intellij.openapi.components.PersistentStateComponent;
import com.intellij.openapi.components.State;
import com.intellij.openapi.components.Storage;
import com.intellij.util.xmlb.XmlSerializerUtil;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

@State(
    name = "com.mem0.jetbrains.settings.Mem0Settings",
    storages = @Storage("Mem0Settings.xml")
)
public class Mem0Settings implements PersistentStateComponent<Mem0Settings> {
    public String serverUrl = "http://127.0.0.1:13370";
    public String mem0CliPath = "";
    public String defaultContext = "";
    public boolean autoDetectContext = true;

    public static Mem0Settings getInstance() {
        return ApplicationManager.getApplication().getService(Mem0Settings.class);
    }

    @Nullable
    @Override
    public Mem0Settings getState() {
        return this;
    }

    @Override
    public void loadState(@NotNull Mem0Settings state) {
        XmlSerializerUtil.copyBean(state, this);
    }

    public String getServerUrl() {
        return serverUrl;
    }

    public void setServerUrl(String serverUrl) {
        this.serverUrl = serverUrl;
    }

    public String getMem0CliPath() {
        return mem0CliPath;
    }

    public void setMem0CliPath(String mem0CliPath) {
        this.mem0CliPath = mem0CliPath;
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
