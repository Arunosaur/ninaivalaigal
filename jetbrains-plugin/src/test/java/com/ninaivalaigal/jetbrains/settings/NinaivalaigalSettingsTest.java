package com.ninaivalaigal.jetbrains.settings;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for NinaivalaigalSettings
 */
class NinaivalaigalSettingsTest {

    private NinaivalaigalSettings settings;

    @BeforeEach
    void setUp() {
        settings = new NinaivalaigalSettings();
    }

    @Test
    void testDefaultValues() {
        assertEquals("", settings.getMcpServerPath());
        assertEquals("", settings.getDefaultContext());
        assertTrue(settings.isAutoDetectContext());
    }

    @Test
    void testSetMcpServerPath() {
        String testPath = "/path/to/mcp/server.py";
        settings.setMcpServerPath(testPath);
        assertEquals(testPath, settings.getMcpServerPath());
    }

    @Test
    void testSetDefaultContext() {
        String testContext = "test-context";
        settings.setDefaultContext(testContext);
        assertEquals(testContext, settings.getDefaultContext());
    }

    @Test
    void testSetAutoDetectContext() {
        settings.setAutoDetectContext(false);
        assertFalse(settings.isAutoDetectContext());

        settings.setAutoDetectContext(true);
        assertTrue(settings.isAutoDetectContext());
    }

    @Test
    void testGetState() {
        NinaivalaigalSettings state = settings.getState();
        assertNotNull(state);
        assertEquals(settings, state);
    }

    @Test
    void testLoadState() {
        NinaivalaigalSettings newState = new NinaivalaigalSettings();
        newState.setMcpServerPath("/new/path");
        newState.setDefaultContext("new-context");
        newState.setAutoDetectContext(false);

        settings.loadState(newState);

        assertEquals("/new/path", settings.getMcpServerPath());
        assertEquals("new-context", settings.getDefaultContext());
        assertFalse(settings.isAutoDetectContext());
    }
}
