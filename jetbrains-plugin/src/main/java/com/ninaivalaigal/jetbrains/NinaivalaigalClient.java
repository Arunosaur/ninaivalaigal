package com.ninaivalaigal.jetbrains;

import com.intellij.openapi.project.Project;
import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * Ninaivalaigal MCP Client for JetBrains IDEs
 * Thin client wrapper around ninaivalaigal's native MCP server
 */
public class NinaivalaigalClient {
    private Process mcpProcess;
    private OutputStreamWriter mcpInput;
    private BufferedReader mcpOutput;
    private String currentContext;
    private int requestId = 1;
    private final String mcpServerPath;
    private final NinaivalaigalSettings settings;

    public NinaivalaigalClient(Project project, NinaivalaigalSettings settings) {
        this.settings = settings;
        this.mcpServerPath = settings.getMcpServerPath();
        this.currentContext = detectProjectContext(project);
        initializeMCPConnection();
    }

    private void initializeMCPConnection() {
        try {
            // Use ninaivalaigal MCP server (configurable path)
            ProcessBuilder pb = new ProcessBuilder("python3", mcpServerPath);
            mcpProcess = pb.start();
            mcpInput = new OutputStreamWriter(mcpProcess.getOutputStream());
            mcpOutput = new BufferedReader(new InputStreamReader(mcpProcess.getInputStream()));

            // Send initialize request (MCP protocol)
            JSONObject initRequest = new JSONObject();
            initRequest.put("jsonrpc", "2.0");
            initRequest.put("id", requestId++);
            initRequest.put("method", "initialize");

            JSONObject params = new JSONObject();
            params.put("protocolVersion", "2024-11-05");

            JSONObject clientInfo = new JSONObject();
            clientInfo.put("name", "ninaivalaigal-jetbrains");
            clientInfo.put("version", "1.0.0");
            params.put("clientInfo", clientInfo);

            JSONObject capabilities = new JSONObject();
            params.put("capabilities", capabilities);

            initRequest.put("params", params);

            sendMCPRequest(initRequest);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private String detectProjectContext(Project project) {
        if (project != null && project.getBasePath() != null) {
            String context = Paths.get(project.getBasePath()).getFileName().toString();
            return settings.isAutoDetectContext() ? context : (settings.getDefaultContext().isEmpty() ? context : settings.getDefaultContext());
        }
        return "ninaivalaigal-session";
    }

    public void setContext(String context) {
        this.currentContext = context;
    }

    public String getCurrentContext() {
        return currentContext;
    }

    public boolean startContext(String contextName) {
        try {
            JSONObject request = new JSONObject();
            request.put("jsonrpc", "2.0");
            request.put("id", requestId++);
            request.put("method", "tools/call");

            JSONObject params = new JSONObject();
            params.put("name", "context_start");

            JSONObject arguments = new JSONObject();
            arguments.put("context_name", contextName);
            params.put("arguments", arguments);

            request.put("params", params);

            JSONObject response = sendMCPRequest(request);
            if (response != null && !response.has("error")) {
                this.currentContext = contextName;
                return true;
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return false;
    }

    public List<String> listContexts() {
        List<String> contexts = new ArrayList<>();
        try {
            JSONObject request = new JSONObject();
            request.put("jsonrpc", "2.0");
            request.put("id", requestId++);
            request.put("method", "tools/call");

            JSONObject params = new JSONObject();
            params.put("name", "list_contexts");
            params.put("arguments", new JSONObject());

            request.put("params", params);

            JSONObject response = sendMCPRequest(request);
            if (response != null && response.has("result")) {
                JSONObject result = response.getJSONObject("result");
                if (result.has("content")) {
                    JSONArray content = result.getJSONArray("content");
                    if (content.length() > 0) {
                        Object contextData = content.getJSONObject(0).get("text");
                        if (contextData instanceof JSONArray) {
                            JSONArray contextArray = (JSONArray) contextData;
                            for (int i = 0; i < contextArray.length(); i++) {
                                contexts.add(contextArray.getString(i));
                            }
                        }
                    }
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return contexts;
    }

    public boolean remember(String memory) {
        try {
            JSONObject request = new JSONObject();
            request.put("jsonrpc", "2.0");
            request.put("id", requestId++);
            request.put("method", "tools/call");

            JSONObject params = new JSONObject();
            params.put("name", "remember");

            JSONObject arguments = new JSONObject();
            arguments.put("text", memory);
            arguments.put("context", currentContext);
            params.put("arguments", arguments);

            request.put("params", params);

            JSONObject response = sendMCPRequest(request);
            return response != null && !response.has("error");
        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
    }

    public String recall() {
        try {
            JSONObject request = new JSONObject();
            request.put("jsonrpc", "2.0");
            request.put("id", requestId++);
            request.put("method", "tools/call");

            JSONObject params = new JSONObject();
            params.put("name", "recall");

            JSONObject arguments = new JSONObject();
            arguments.put("context", currentContext);
            params.put("arguments", arguments);

            request.put("params", params);

            JSONObject response = sendMCPRequest(request);
            if (response != null && response.has("result")) {
                JSONObject result = response.getJSONObject("result");
                if (result.has("content")) {
                    JSONArray content = result.getJSONArray("content");
                    if (content.length() > 0) {
                        return content.getJSONObject(0).getString("text");
                    }
                }
            }
            return "No memories found";
        } catch (Exception e) {
            e.printStackTrace();
            return "Error recalling memories: " + e.getMessage();
        }
    }

    public boolean isServerRunning() {
        return mcpProcess != null && mcpProcess.isAlive();
    }

    private JSONObject sendMCPRequest(JSONObject request) {
        try {
            String requestStr = request.toString() + "\n";
            mcpInput.write(requestStr);
            mcpInput.flush();

            String responseStr = mcpOutput.readLine();
            if (responseStr != null) {
                return new JSONObject(responseStr);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    public void close() {
        try {
            if (mcpInput != null) mcpInput.close();
            if (mcpOutput != null) mcpOutput.close();
            if (mcpProcess != null) mcpProcess.destroy();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
