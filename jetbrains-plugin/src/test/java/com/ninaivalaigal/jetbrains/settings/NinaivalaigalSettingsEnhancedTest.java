package com.ninaivalaigal.jetbrains.settings;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Enhanced unit tests for NinaivalaigalSettings
 * Tests settings persistence, validation, and configuration
 */
class NinaivalaigalSettingsEnhancedTest {

    private NinaivalaigalSettings settings;

    @BeforeEach
    void setUp() {
        // Create a new instance for testing (not using singleton)
        settings = new NinaivalaigalSettings();
    }

    @Test
    void testDefaultValues() {
        // Test default values after construction
        assertEquals("", settings.getMcpServerPath());
        assertEquals("", settings.getDefaultContext());
        assertTrue(settings.isAutoDetectContext());
    }

    @Test
    void testMcpServerPathGetterAndSetter() {
        // Test MCP server path getter and setter
        String testPath = "/path/to/mcp/server.py";
        settings.setMcpServerPath(testPath);

        assertEquals(testPath, settings.getMcpServerPath());
    }

    @Test
    void testMcpServerPathEmpty() {
        // Test edge case: empty MCP server path
        settings.setMcpServerPath("");

        String path = settings.getMcpServerPath();
        assertNotNull(path);
        assertTrue(path.isEmpty());
    }

    @Test
    void testMcpServerPathWithSpecialCharacters() {
        // Test MCP server path with special characters
        String pathWithSpecialChars = "/path/to/mcp/server-v1.0.0.py";
        settings.setMcpServerPath(pathWithSpecialChars);

        String path = settings.getMcpServerPath();
        assertNotNull(path);
        assertEquals(pathWithSpecialChars, path);
        assertTrue(path.contains("server-v1.0.0"));
    }

    @Test
    void testAutoDetectContextGetterAndSetter() {
        // Test auto-detect context setting
        settings.setAutoDetectContext(true);
        assertTrue(settings.isAutoDetectContext());

        settings.setAutoDetectContext(false);
        assertFalse(settings.isAutoDetectContext());
    }

    @Test
    void testDefaultContextGetterAndSetter() {
        // Test default context setting
        String defaultContext = "default-context";
        settings.setDefaultContext(defaultContext);

        String context = settings.getDefaultContext();
        assertNotNull(context);
        assertEquals(defaultContext, context);
    }

    @Test
    void testDefaultContextEmpty() {
        // Test edge case: empty default context
        settings.setDefaultContext("");

        String context = settings.getDefaultContext();
        assertNotNull(context);
        assertTrue(context.isEmpty());
    }

    @Test
    void testDefaultContextWithSpecialCharacters() {
        // Test default context with special characters
        String contextWithSpecialChars = "context_with-special.chars_123";
        settings.setDefaultContext(contextWithSpecialChars);

        String context = settings.getDefaultContext();
        assertNotNull(context);
        assertEquals(contextWithSpecialChars, context);
    }

    @Test
    void testSettingsCombination() {
        // Test combination of settings
        settings.setMcpServerPath("/path/to/server.py");
        settings.setAutoDetectContext(true);
        settings.setDefaultContext("default-context");

        assertEquals("/path/to/server.py", settings.getMcpServerPath());
        assertTrue(settings.isAutoDetectContext());
        assertEquals("default-context", settings.getDefaultContext());
    }

    @Test
    void testSettingsPersistence() {
        // Test that settings can be retrieved after setting
        String testPath = "/test/path/server.py";
        settings.setMcpServerPath(testPath);

        String savedPath = settings.getMcpServerPath();
        assertEquals(testPath, savedPath);
    }

    @Test
    void testSettingsWithLongValues() {
        // Test settings with long values
        StringBuilder longPath = new StringBuilder();
        for (int i = 0; i < 100; i++) {
            longPath.append("/very/long/path/");
        }
        longPath.append("server.py");

        settings.setMcpServerPath(longPath.toString());

        String path = settings.getMcpServerPath();
        assertNotNull(path);
        assertTrue(path.length() > 100);
        assertEquals(longPath.toString(), path);
    }

    @Test
    void testMultipleSettingsReads() {
        // Test multiple reads of settings
        settings.setMcpServerPath("/path/to/server.py");

        String path1 = settings.getMcpServerPath();
        String path2 = settings.getMcpServerPath();
        String path3 = settings.getMcpServerPath();

        assertEquals(path1, path2);
        assertEquals(path2, path3);
        assertEquals("/path/to/server.py", path1);
    }

    @Test
    void testLoadState() {
        // Test loadState method
        NinaivalaigalSettings newState = new NinaivalaigalSettings();
        newState.setMcpServerPath("/new/path/server.py");
        newState.setAutoDetectContext(false);
        newState.setDefaultContext("new-context");

        settings.loadState(newState);

        assertEquals("/new/path/server.py", settings.getMcpServerPath());
        assertFalse(settings.isAutoDetectContext());
        assertEquals("new-context", settings.getDefaultContext());
    }

    @Test
    void testGetState() {
        // Test getState method returns this instance
        settings.setMcpServerPath("/test/path");
        NinaivalaigalSettings state = settings.getState();

        assertSame(settings, state);
        assertEquals("/test/path", state.getMcpServerPath());
    }

    @Test
    void testSettingsModification() {
        // Test that modifying settings works correctly
        settings.setMcpServerPath("/initial/path");
        assertEquals("/initial/path", settings.getMcpServerPath());

        settings.setMcpServerPath("/updated/path");
        assertEquals("/updated/path", settings.getMcpServerPath());
    }
}
