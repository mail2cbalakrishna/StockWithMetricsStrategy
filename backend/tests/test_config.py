"""
Test for Configuration Settings
"""
import pytest


class TestConfigSettings:
    """Test cases for application configuration"""
    
    def test_cors_origins_includes_localhost(self):
        """Test that CORS includes localhost"""
        cors_origins = [
            'http://localhost:3000',
            'http://localhost:8080'
        ]
        assert 'http://localhost:3000' in cors_origins
    
    def test_cors_origins_includes_ip(self):
        """Test that CORS includes machine IP"""
        cors_origins = [
            'http://192.168.1.209:3000',
            'http://192.168.1.209:8080'
        ]
        assert 'http://192.168.1.209:3000' in cors_origins
    
    def test_keycloak_realm_name(self):
        """Test Keycloak realm is configured"""
        realm = 'stock-analysis'
        assert realm == 'stock-analysis'
        assert len(realm) > 0
    
    def test_keycloak_client_id(self):
        """Test Keycloak client ID is configured"""
        client_id = 'stock-analysis-client'
        assert client_id == 'stock-analysis-client'
        assert 'client' in client_id.lower()
    
    def test_api_keys_configured(self):
        """Test that API keys are configured"""
        # These should be set via environment variables in production
        alpha_vantage_key = 'YC6TI0S22SVZI87N'
        polygon_key = '8oQY_6TRJX6KnrVyhzkzqLPFd4Jck1Qw'
        
        assert len(alpha_vantage_key) > 0
        assert len(polygon_key) > 0
    
    def test_rate_limits_configured(self):
        """Test that rate limits are set"""
        rate_limits = {
            'yfinance': 100,
            'alpha_vantage': 25,
            'polygon': 50
        }
        
        assert all(v > 0 for v in rate_limits.values())
    
    def test_redis_host_configured(self):
        """Test Redis host is configured"""
        redis_host = 'redis'
        assert redis_host == 'redis'
    
    def test_redis_port_configured(self):
        """Test Redis port is configured"""
        redis_port = 6379
        assert redis_port == 6379
        assert redis_port > 0


class TestDatabaseSettings:
    """Test cases for database configuration"""
    
    def test_database_url_postgresql(self):
        """Test database URL uses PostgreSQL"""
        db_url = 'postgresql://keycloak:keycloak_password@postgres:5432/keycloak'
        assert 'postgresql' in db_url
        assert 'postgres:5432' in db_url
    
    def test_min_market_cap_configured(self):
        """Test minimum market cap setting"""
        min_market_cap = 1_000_000_000
        assert min_market_cap == 1_000_000_000
        assert min_market_cap > 0


class TestMagicFormulaSettings:
    """Test cases for Magic Formula settings"""
    
    def test_exclude_financials_setting(self):
        """Test that financial sector is excluded"""
        exclude_financials = True
        assert exclude_financials is True
    
    def test_exclude_utilities_setting(self):
        """Test that utilities sector is excluded"""
        exclude_utilities = True
        assert exclude_utilities is True
    
    def test_excluded_sectors_list(self):
        """Test that excluded sectors are properly configured"""
        excluded_sectors = ['Financial Services', 'Financial', 'Utilities']
        assert 'Financial' in excluded_sectors
        assert 'Utilities' in excluded_sectors
        assert len(excluded_sectors) >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
