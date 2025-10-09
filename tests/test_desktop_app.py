from __future__ import annotations

import threading
import time
import pytest
import requests
from unittest.mock import patch, MagicMock

from src.desktop.app import start_server, main, build_desktop


class TestDesktopApp:
    """Test the desktop application functionality"""
    
    def test_start_server_function(self):
        """Test that start_server function exists and is callable"""
        assert callable(start_server)
    
    def test_build_desktop_function(self):
        """Test the build_desktop function"""
        # Capture print output
        with patch('builtins.print') as mock_print:
            build_desktop()
            
        # Verify that build instructions were printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Building desktop application" in call for call in print_calls)
        assert any("PyInstaller" in call for call in print_calls)
    
    @patch('src.desktop.app.webview')
    @patch('src.desktop.app.threading.Thread')
    @patch('src.desktop.app.time.sleep')
    def test_main_function_setup(self, mock_sleep, mock_thread, mock_webview):
        """Test that main function sets up correctly"""
        # Mock the thread and webview
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        mock_window = MagicMock()
        mock_webview.create_window.return_value = mock_window
        
        # Call main function
        main()
        
        # Verify thread was created and started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        
        # Verify sleep was called to wait for server
        mock_sleep.assert_called_once_with(2)
        
        # Verify webview window was created (URL includes desktop flag and js_api is provided)
        assert mock_webview.create_window.call_count == 1
        call_args = mock_webview.create_window.call_args
        assert call_args[0][0] == "TDMS Desktop Application"
        assert "127.0.0.1:8000" in call_args[0][1]
        assert call_args[1]["width"] == 1200
        assert call_args[1]["height"] == 800
        assert call_args[1]["min_size"] == (800, 600)
        assert call_args[1]["resizable"] == True
        assert "js_api" in call_args[1]  # Verify js_api is provided
        
        # Verify webview was started
        mock_webview.start.assert_called_once_with(debug=False, gui='edgechromium')


class TestDesktopAppIntegration:
    """Integration tests for the desktop application"""
    
    @pytest.fixture(scope="class")
    def desktop_server(self):
        """Start the desktop server for integration testing"""
        # Start server in a separate thread
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(3)
        
        # Verify server is running
        max_retries = 10
        for i in range(max_retries):
            try:
                response = requests.get("http://127.0.0.1:8000/", timeout=1)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                if i < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    pytest.skip("Could not start desktop server for testing")
        
        yield "http://127.0.0.1:8000"
        
        # Cleanup is automatic since thread is daemon
    
    def test_server_responds(self, desktop_server):
        """Test that the desktop server responds to requests"""
        response = requests.get(f"{desktop_server}/")
        assert response.status_code == 200
        assert "Table Database" in response.text
    
    def test_api_endpoints_available(self, desktop_server):
        """Test that API endpoints are available through desktop server"""
        # Test databases endpoint
        response = requests.get(f"{desktop_server}/databases")
        assert response.status_code == 200
        data = response.json()
        assert "active" in data
        assert "databases" in data
    
    def test_create_table_through_desktop(self, desktop_server):
        """Test creating a table through the desktop server"""
        schema = [
            {"name": "id", "type": "integer"},
            {"name": "name", "type": "string"}
        ]
        
        response = requests.post(f"{desktop_server}/create_table", json={
            "name": "desktop_test_table",
            "schema": schema
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["table"]["name"] == "desktop_test_table"
    
    def test_insert_row_through_desktop(self, desktop_server):
        """Test inserting a row through the desktop server"""
        # First create a table
        schema = [{"name": "id", "type": "integer"}, {"name": "value", "type": "string"}]
        requests.post(f"{desktop_server}/create_table", json={
            "name": "insert_test_table",
            "schema": schema
        })
        
        # Then insert a row
        response = requests.post(f"{desktop_server}/insert_row", json={
            "table": "insert_test_table",
            "values": {"id": 1, "value": "test"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_union_operation_through_desktop(self, desktop_server):
        """Test union operation through the desktop server"""
        # Create two tables
        schema = [{"name": "id", "type": "integer"}, {"name": "name", "type": "string"}]
        
        requests.post(f"{desktop_server}/create_table", json={
            "name": "union_table1",
            "schema": schema
        })
        
        requests.post(f"{desktop_server}/create_table", json={
            "name": "union_table2", 
            "schema": schema
        })
        
        # Add data to tables
        requests.post(f"{desktop_server}/insert_row", json={
            "table": "union_table1",
            "values": {"id": 1, "name": "Alice"}
        })
        
        requests.post(f"{desktop_server}/insert_row", json={
            "table": "union_table2",
            "values": {"id": 2, "name": "Bob"}
        })
        
        # Perform union
        response = requests.post(f"{desktop_server}/union", json={
            "left": "union_table1",
            "right": "union_table2",
            "name": "union_result"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "union_result"
        assert len(data["rows"]) == 2
    
    def test_list_tables_through_desktop(self, desktop_server):
        """Test listing tables through the desktop server"""
        response = requests.get(f"{desktop_server}/tables")
        assert response.status_code == 200
        data = response.json()
        assert "tables" in data
        assert isinstance(data["tables"], list)
    
    def test_desktop_persistence(self, desktop_server, tmp_path):
        """Test database persistence through desktop server"""
        # Create a table with data
        schema = [{"name": "id", "type": "integer"}, {"name": "data", "type": "string"}]
        requests.post(f"{desktop_server}/create_table", json={
            "name": "persist_test",
            "schema": schema
        })
        
        requests.post(f"{desktop_server}/insert_row", json={
            "table": "persist_test",
            "values": {"id": 1, "data": "test_data"}
        })
        
        # Save database
        file_path = str(tmp_path / "desktop_test.json")
        response = requests.post(f"{desktop_server}/save", json={
            "path": file_path
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        
        # Verify file was created
        assert (tmp_path / "desktop_test.json").exists()


class TestDesktopAppErrorHandling:
    """Test error handling in the desktop application"""
    
    def test_invalid_server_port_handling(self):
        """Test handling of server startup issues"""
        # This test verifies that the app handles server startup gracefully
        # In a real scenario, you might test port conflicts, etc.
        with patch('src.desktop.app.uvicorn.run') as mock_uvicorn:
            mock_uvicorn.side_effect = Exception("Port already in use")
            
            # The function should handle the exception gracefully
            try:
                start_server()
            except Exception as e:
                # The exception should be the one we mocked
                assert "Port already in use" in str(e)
    
    @patch('src.desktop.app.webview')
    def test_webview_creation_error(self, mock_webview):
        """Test handling of webview creation errors"""
        mock_webview.create_window.side_effect = Exception("Webview error")
        
        with pytest.raises(Exception) as exc_info:
            with patch('src.desktop.app.threading.Thread'):
                with patch('src.desktop.app.time.sleep'):
                    main()
        
        assert "Webview error" in str(exc_info.value)


class TestDesktopAppConfiguration:
    """Test desktop application configuration"""
    
    def test_server_configuration(self):
        """Test that server is configured correctly"""
        # Test that the server configuration matches expectations
        with patch('src.desktop.app.uvicorn.run') as mock_uvicorn:
            start_server()
            
            # Verify uvicorn was called with correct parameters
            mock_uvicorn.assert_called_once()
            args, kwargs = mock_uvicorn.call_args
            
            # Check the app parameter
            assert args[0].__name__ == 'app'  # FastAPI app
            
            # Check keyword arguments
            assert kwargs['host'] == "127.0.0.1"
            assert kwargs['port'] == 8000
            assert kwargs['log_level'] == "warning"
    
    def test_window_configuration(self):
        """Test that webview window is configured correctly"""
        with patch('src.desktop.app.webview') as mock_webview:
            with patch('src.desktop.app.threading.Thread'):
                with patch('src.desktop.app.time.sleep'):
                    main()
            
            # Verify window configuration
            mock_webview.create_window.assert_called_once_with(
                "TDMS Desktop Application",
                "http://127.0.0.1:8000",
                width=1200,
                height=800,
                min_size=(800, 600),
                resizable=True
            )


# Performance and stress tests
class TestDesktopAppPerformance:
    """Performance tests for the desktop application"""
    
    @pytest.mark.slow
    def test_server_startup_time(self):
        """Test that server starts within reasonable time"""
        import time
        
        start_time = time.time()
        
        # Start server in thread
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Wait for server to be ready
        max_wait = 10  # seconds
        server_ready = False
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get("http://127.0.0.1:8000/", timeout=1)
                if response.status_code == 200:
                    server_ready = True
                    break
            except requests.exceptions.RequestException:
                time.sleep(0.1)
        
        startup_time = time.time() - start_time
        
        assert server_ready, "Server did not start within reasonable time"
        assert startup_time < 5, f"Server took too long to start: {startup_time:.2f}s"
    
    @pytest.mark.slow
    def test_multiple_requests_handling(self):
        """Test that desktop server can handle multiple concurrent requests"""
        # Start server
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        time.sleep(2)
        
        # Make multiple concurrent requests
        import concurrent.futures
        
        def make_request():
            try:
                response = requests.get("http://127.0.0.1:8000/databases", timeout=5)
                return response.status_code == 200
            except:
                return False
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # At least 80% of requests should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8, f"Success rate too low: {success_rate:.2f}"



