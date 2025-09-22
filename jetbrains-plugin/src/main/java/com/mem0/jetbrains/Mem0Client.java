package com.mem0.jetbrains;

import com.intellij.openapi.project.Project;
import com.intellij.openapi.util.text.StringUtil;
import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

public class Mem0Client {
    private static final String MCP_SERVER_PATH = "/opt/homebrew/anaconda3/bin/python";
    private static final String MCP_SCRIPT_PATH = "/Users/asrajag/Workspace/mem0/server/mcp_server.py";
    private Process mcpProcess;
    private OutputStreamWriter mcpInput;
    private BufferedReader mcpOutput;
    private String currentContext;
    private int requestId = 1;

    public Mem0Client(Project project) {
        this.currentContext = detectProjectContext(project);
        initializeMCPConnection();
    }

    private void initializeMCPConnection() {
        try {
            ProcessBuilder pb = new ProcessBuilder(MCP_SERVER_PATH, MCP_SCRIPT_PATH);
            mcpProcess = pb.start();
            mcpInput = new OutputStreamWriter(mcpProcess.getOutputStream());
            mcpOutput = new BufferedReader(new InputStreamReader(mcpProcess.getInputStream()));

            // Send initialize request
            JSONObject initRequest = new JSONObject();
            initRequest.put("jsonrpc", "2.0");
            initRequest.put("id", requestId++);
            initRequest.put("method", "initialize");

            JSONObject params = new JSONObject();
            params.put("protocolVersion", "2024-11-05");

            JSONObject clientInfo = new JSONObject();
            clientInfo.put("name", "mem0-jetbrains");
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
            return Paths.get(project.getBasePath()).getFileName().toString();
        }
        return "jetbrains-session";
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
