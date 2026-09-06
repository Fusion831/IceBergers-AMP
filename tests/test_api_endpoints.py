"""Integration tests for all FastAPI REST endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from main import app


@pytest.mark.asyncio
async def test_api_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["mock_mode"] is True


@pytest.mark.asyncio
async def test_api_missions_workflow(sample_mission_create):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Mission
        create_payload = sample_mission_create.model_dump(mode="json")
        resp = await ac.post("/api/v1/missions", json=create_payload)
        assert resp.status_code == 201
        m_data = resp.json()
        mission_id = m_data["id"]

        # 2. Get Mission
        resp = await ac.get(f"/api/v1/missions/{mission_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == mission_id

        # 3. Analyze Mission
        resp = await ac.post(f"/api/v1/missions/{mission_id}/analyze")
        assert resp.status_code == 200
        analysis_data = resp.json()
        assert len(analysis_data["routes"]) == 5

        # 4. Get Analysis
        resp = await ac.get(f"/api/v1/missions/{mission_id}/analysis")
        assert resp.status_code == 200
        assert len(resp.json()["routes"]) == 5


@pytest.mark.asyncio
async def test_api_environment():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Slice
        resp = await ac.get("/api/v1/environment/slice?min_lat=-70&max_lat=-60&min_lon=60&max_lon=80")
        assert resp.status_code == 200
        assert "sea_surface_temperature_c" in resp.json()["layers"]

        # Point
        resp = await ac.get("/api/v1/environment/point?lat=-65.0&lon=70.0")
        assert resp.status_code == 200
        assert "wave_height_m" in resp.json()


@pytest.mark.asyncio
async def test_api_sea_ice():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Forecast
        resp = await ac.get("/api/v1/sea-ice/forecast?horizon_days=14")
        assert resp.status_code == 200
        assert "uncertainty" in resp.json()

        # Baselines
        resp = await ac.get("/api/v1/sea-ice/baselines?horizon_days=14")
        assert resp.status_code == 200
        assert "persistence" in resp.json()


@pytest.mark.asyncio
async def test_api_icebergs():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # List
        resp = await ac.get("/api/v1/icebergs")
        assert resp.status_code == 200
        icebergs = resp.json()
        assert len(icebergs) > 0

        ib_id = icebergs[0]["iceberg_id"]
        # Trajectory
        resp = await ac.get(f"/api/v1/icebergs/{ib_id}/trajectory?forecast_days=10&ensemble_size=20")
        assert resp.status_code == 200
        assert resp.json()["ensemble_size"] == 20


@pytest.mark.asyncio
async def test_api_risk_map():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/risk/map?horizon_days=14")
        assert resp.status_code == 200
        assert "mean_risk" in resp.json()


@pytest.mark.asyncio
async def test_api_routes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        opt_req = {
            "origin": {"latitude": -55.0, "longitude": 65.0},
            "destination": {"latitude": -69.4, "longitude": 76.2},
            "departure_time": "2026-01-15T00:00:00Z",
        }
        resp = await ac.post("/api/v1/routes/optimize", json=opt_req)
        assert resp.status_code == 200
        routes = resp.json()["routes"]
        assert len(routes) == 5

        # Compare
        comp_req = {"route_ids": [r["route_id"] for r in routes]}
        resp = await ac.post("/api/v1/routes/compare", json=comp_req)
        assert resp.status_code == 200
        assert "fastest_route_id" in resp.json()


@pytest.mark.asyncio
async def test_api_stations():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/stations/accessibility?station_name=Bharati")
        assert resp.status_code == 200
        assert len(resp.json()["accessibility_points"]) > 0


@pytest.mark.asyncio
async def test_api_historical():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        hist_req = {"historical_cutoff": "2026-01-01T00:00:00Z"}
        resp = await ac.post("/api/v1/historical/evaluate", json=hist_req)
        assert resp.status_code == 200
        assert resp.json()["leakage_check_passed"] is True


@pytest.mark.asyncio
async def test_api_jobs():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/jobs/test-job-001")
        assert resp.status_code == 200
        assert resp.json()["job_id"] == "test-job-001"
