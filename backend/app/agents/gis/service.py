"""GIS agent — builds Leaflet-ready map layers and evaluates the AOI geofence.

Doesn't call any external API: it takes the AOI plus whatever geo-tagged features the
other agents (news, vision, rag) produced for this query, and decides which of them
fall inside the AOI's radius. Runs standalone too (AOI marker + empty geofence) so it
can be exercised on its own during development.
"""
from __future__ import annotations

from app.core.geo import haversine_km
from app.models.schemas import AgentEnvelope, AgentName, AgentStatus, AOI, GeoFeature, GeofenceStatus, GISResult


def evaluate_geofence(aoi: AOI, features: list[GeoFeature]) -> list[GeofenceStatus]:
    statuses = []
    for f in features:
        distance = haversine_km(aoi.lat, aoi.lon, f.lat, f.lon)
        statuses.append(
            GeofenceStatus(feature_id=f.id, inside_zone=distance <= aoi.radius_km, distance_km=round(distance, 2))
        )
    return statuses


def build_gis_result(aoi: AOI, features: list[GeoFeature] | None = None) -> GISResult:
    features = features or []
    aoi_feature = GeoFeature(
        id="aoi-center", lat=aoi.lat, lon=aoi.lon, label=aoi.name, layer="aoi", source_agent=AgentName.gis
    )
    all_features = [aoi_feature, *features]
    return GISResult(aoi=aoi, features=all_features, geofence_statuses=evaluate_geofence(aoi, features))


async def fetch_gis(aoi: AOI, features: list[GeoFeature] | None = None) -> AgentEnvelope:
    result = build_gis_result(aoi, features)
    return AgentEnvelope(agent=AgentName.gis, status=AgentStatus.ok, data=result.model_dump())
