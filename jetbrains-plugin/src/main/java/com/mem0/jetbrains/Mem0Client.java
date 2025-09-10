package com.mem0.jetbrains;

import com.intellij.openapi.project.Project;
import com.intellij.openapi.util.text.StringUtil;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.util.EntityUtils;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

public class Mem0Client {
    private static final String DEFAULT_SERVER_URL = "http://127.0.0.1:13370";
    private final String serverUrl;
    private final String mem0CliPath;
    private String currentContext;

    public Mem0Client(Project project) {
        this.serverUrl = Mem0Settings.getInstance().getServerUrl();
        this.mem0CliPath = findMem0Cli();
        this.currentContext = detectProjectContext(project);
    }

    private String findMem0Cli() {
        // Try common locations for mem0 CLI
        String[] possiblePaths = {
            System.getProperty("user.home") + "/Workspace/mem0/client/mem0",
            System.getProperty("user.home") + "/workspace/mem0/client/mem0",
            System.getProperty("user.home") + "/Projects/mem0/client/mem0",
            "/usr/local/bin/mem0",
            "mem0" // Try PATH
        };

        for (String path : possiblePaths) {
            if (new File(path).exists()) {
                return path;
            }
        }
        return "mem0"; // Fallback to PATH
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
            ProcessBuilder pb = new ProcessBuilder(mem0CliPath, "context", "start", contextName);
            pb.environment().put("MEM0_CONTEXT", contextName);
            Process process = pb.start();
            int exitCode = process.waitFor();
            
            if (exitCode == 0) {
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
            ProcessBuilder pb = new ProcessBuilder(mem0CliPath, "contexts");
            Process process = pb.start();
            
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                if (!StringUtil.isEmpty(line.trim())) {
                    contexts.add(line.trim());
                }
            }
            process.waitFor();
        } catch (Exception e) {
            e.printStackTrace();
        }
        return contexts;
    }

    public boolean remember(String memory) {
        try {
            ProcessBuilder pb = new ProcessBuilder(mem0CliPath, "remember", memory, "--context", currentContext);
            pb.environment().put("MEM0_CONTEXT", currentContext);
            Process process = pb.start();
            return process.waitFor() == 0;
        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
    }

    public String recall() {
        try {
            ProcessBuilder pb = new ProcessBuilder(mem0CliPath, "recall", "--context", currentContext);
            pb.environment().put("MEM0_CONTEXT", currentContext);
            Process process = pb.start();
            
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuilder result = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                result.append(line).append("\n");
            }
            process.waitFor();
            return result.toString();
        } catch (Exception e) {
            e.printStackTrace();
            return "Error recalling memories: " + e.getMessage();
        }
    }

    public boolean isServerRunning() {
        try (CloseableHttpClient client = HttpClients.createDefault()) {
            HttpGet request = new HttpGet(serverUrl + "/");
            try (CloseableHttpResponse response = client.execute(request)) {
                return response.getStatusLine().getStatusCode() == 200;
            }
        } catch (Exception e) {
            return false;
        }
    }
}
