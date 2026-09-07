import os
import numpy as np
import pandas as pd
import xarray as xr
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
import joblib
import datetime

os.makedirs('src', exist_ok=True)
os.makedirs('scripts', exist_ok=True)
os.makedirs('models', exist_ok=True)

class IceKNNSouthModel:
    def __init__(self, k_neighbors=30, n_components=10, search_window_days=30):
        self.k_neighbors = k_neighbors
        self.n_components = n_components
        self.search_window_days = search_window_days
        self.climatology = {}
        self.pcas = {}
        self.historical_features = None
        self.historical_targets = None
        self.historical_dates = None
        self.lat = None
        self.lon = None
        self.is_fitted = False

    def _compute_dayofyear(self, dates):
        doy = dates.dayofyear
        return np.where(doy == 366, 365, doy)

    def fit(self, sic, era5, ocean, dates, lat, lon):
        self.lat = lat
        self.lon = lon
        doy = self._compute_dayofyear(dates)
        unique_doy = np.arange(1, 366)
        
        variables = {'sic': sic}
        variables.update(era5)
        variables.update(ocean)
        
        self.climatology = {v: np.zeros((366, len(lat), len(lon))) for v in variables}
        anomalies = {v: np.zeros_like(data) for v, data in variables.items()}
        
        for d in unique_doy:
            mask = (doy == d)
            if not np.any(mask):
                continue
            for v, data in variables.items():
                mean_field = np.nanmean(data[mask], axis=0)
                self.climatology[v][d] = mean_field
                anomalies[v][mask] = data[mask] - mean_field
                
        historical_features_list = []
        for v, anom_data in anomalies.items():
            flattened = anom_data.reshape(anom_data.shape[0], -1)
            flattened = np.nan_to_num(flattened, nan=0.0)
            pca = PCA(n_components=self.n_components, svd_solver='randomized')
            scores = pca.fit_transform(flattened)
            std = np.std(scores, axis=0)
            std[std == 0] = 1.0
            scores = scores / std
            self.pcas[v] = {'model': pca, 'std': std}
            historical_features_list.append(scores)
            
        self.historical_features = np.hstack(historical_features_list)
        self.historical_targets = anomalies['sic']
        self.historical_dates = dates
        self.is_fitted = True

    def _drift_ice_correction(self, predicted_sic, predicted_sica, sst):
        if sst is not None:
            mask = (sst > -1.0) & (predicted_sic < 15.0)
            predicted_sic[mask] = 0.0
            predicted_sica[mask] = 0.0
        return predicted_sic, predicted_sica
        
    def predict(self, initial_date, initial_sic, current_era5, current_ocean, lead_days=90):
        if not self.is_fitted:
            raise ValueError('Model must be fitted before prediction.')
            
        initial_date = pd.to_datetime(initial_date)
        doy = self._compute_dayofyear(pd.DatetimeIndex([initial_date]))[0]
        
        variables = {'sic': initial_sic}
        variables.update(current_era5)
        variables.update(current_ocean)
        
        current_features_list = []
        for v, data in variables.items():
            anom = data - self.climatology[v][doy]
            flattened = np.nan_to_num(anom.reshape(1, -1), nan=0.0)
            scores = self.pcas[v]['model'].transform(flattened)
            scores = scores / self.pcas[v]['std']
            current_features_list.append(scores)
            
        current_features = np.hstack(current_features_list)
        
        hist_doy = self._compute_dayofyear(self.historical_dates)
        diff = np.abs(hist_doy - doy)
        diff = np.minimum(diff, 365 - diff)
        valid_indices = np.where(diff <= self.search_window_days)[0]
        max_idx = len(self.historical_dates) - lead_days - 1
        valid_indices = valid_indices[valid_indices <= max_idx]
        
        search_features = self.historical_features[valid_indices]
        knn = NearestNeighbors(n_neighbors=self.k_neighbors, metric='euclidean')
        knn.fit(search_features)
        distances, indices = knn.kneighbors(current_features)
        analog_indices = valid_indices[indices[0]]
        
        weights = 1.0 / (distances[0] + 1e-6)
        weights /= np.sum(weights)
        
        forecast_dates = [initial_date + pd.Timedelta(days=d) for d in range(1, lead_days + 1)]
        forecast_doy = self._compute_dayofyear(pd.DatetimeIndex(forecast_dates))
        
        forecast_sic = np.zeros((lead_days, len(self.lat), len(self.lon)))
        forecast_sica = np.zeros_like(forecast_sic)
        forecast_uncertainty = np.zeros_like(forecast_sic)
        forecast_q05 = np.zeros_like(forecast_sic)
        forecast_q95 = np.zeros_like(forecast_sic)
        forecast_clim = np.zeros_like(forecast_sic)
        
        for i, tau in enumerate(range(1, lead_days + 1)):
            target_indices = analog_indices + tau
            ensemble_sica = self.historical_targets[target_indices]
            
            pred_sica = np.average(ensemble_sica, axis=0, weights=weights)
            variance = np.average((ensemble_sica - pred_sica)**2, axis=0, weights=weights)
            pred_unc = np.sqrt(variance)
            pred_q05 = np.percentile(ensemble_sica, 5, axis=0)
            pred_q95 = np.percentile(ensemble_sica, 95, axis=0)
            
            c_doy = forecast_doy[i]
            clim_sic = self.climatology['sic'][c_doy]
            pred_sic = np.clip(clim_sic + pred_sica, 0.0, 100.0)
            
            pred_sic, pred_sica = self._drift_ice_correction(pred_sic, pred_sica, None)
            
            forecast_sic[i] = pred_sic
            forecast_sica[i] = pred_sica
            forecast_uncertainty[i] = pred_unc
            forecast_q05[i] = np.clip(clim_sic + pred_q05, 0.0, 100.0)
            forecast_q95[i] = np.clip(clim_sic + pred_q95, 0.0, 100.0)
            forecast_clim[i] = clim_sic
            
        return {
            'dates': forecast_dates,
            'sic': forecast_sic,
            'sica': forecast_sica,
            'sic_uncertainty': forecast_uncertainty,
            'sic_q05': forecast_q05,
            'sic_q95': forecast_q95,
            'sic_clim': forecast_clim
        }

    def export_amip_netcdf(self, forecast, output_path, model_name='Ice-kNN-South'):
        times = pd.DatetimeIndex(forecast['dates'])
        lat_bnds = np.zeros((len(self.lat), 2))
        lat_bnds[:, 0] = self.lat - 0.25
        lat_bnds[:, 1] = self.lat + 0.25
        lon_bnds = np.zeros((len(self.lon), 2))
        lon_bnds[:, 0] = self.lon - 0.25
        lon_bnds[:, 1] = self.lon + 0.25
        
        ds = xr.Dataset(
            data_vars=dict(
                sic=(['time', 'lat', 'lon'], forecast['sic'], {'standard_name': 'sea_ice_area_fraction', 'units': '%', '_FillValue': 1.e20, 'long_name': 'Sea Ice Concentration'}),
                sica=(['time', 'lat', 'lon'], forecast['sica'], {'standard_name': 'sea_ice_area_fraction_anomaly', 'units': '%', '_FillValue': 1.e20, 'long_name': 'Sea Ice Concentration Anomaly'}),
                sic_uncertainty=(['time', 'lat', 'lon'], forecast['sic_uncertainty'], {'units': '%', '_FillValue': 1.e20, 'long_name': 'Ensemble Standard Deviation'}),
                sic_q05=(['time', 'lat', 'lon'], forecast['sic_q05'], {'units': '%', '_FillValue': 1.e20, 'long_name': '5th Percentile'}),
                sic_q95=(['time', 'lat', 'lon'], forecast['sic_q95'], {'units': '%', '_FillValue': 1.e20, 'long_name': '95th Percentile'}),
                sic_clim=(['time', 'lat', 'lon'], forecast['sic_clim'], {'units': '%', '_FillValue': 1.e20, 'long_name': 'Climatological SIC'})
            ),
            coords=dict(
                time=(['time'], times, {'standard_name': 'time', 'axis': 'T'}),
                lat=(['lat'], self.lat, {'standard_name': 'latitude', 'units': 'degrees_north', 'axis': 'Y', 'bounds': 'lat_bnds'}),
                lon=(['lon'], self.lon, {'standard_name': 'longitude', 'units': 'degrees_east', 'axis': 'X', 'bounds': 'lon_bnds'})
            ),
            attrs=dict(
                title=f'{model_name} Sea Ice Forecast',
                institution='Google DeepMind Advanced Agentic Coding',
                source='Ice-kNN-South (Lin et al. 2024/2025)',
                references='DOI: 10.1029/2024JH000433',
                conventions='CF-1.7, AMIP',
                history=f'Generated on {datetime.datetime.now().isoformat()}'
            )
        )
        ds['lat_bnds'] = (['lat', 'bnds'], lat_bnds)
        ds['lon_bnds'] = (['lon', 'bnds'], lon_bnds)
        ds.to_netcdf(output_path, format='NETCDF4')
        print(f'AMIP forecast exported to {output_path}')

    def save(self, filepath):
        joblib.dump(self, filepath)
        print(f'Model saved to {filepath}')

    @classmethod
    def load(cls, filepath):
        return joblib.load(filepath)

if __name__ == '__main__':
    with open('src/ice_knn.py', 'w') as f:
        import inspect
        f.write(inspect.getsource(IceKNNSouthModel))

    print('Generating synthetic historical dataset for Antarctic...')
    np.random.seed(42)
    days = 365 * 10
    dates = pd.date_range('2010-01-01', periods=days, freq='D')

    # Coarser grid to avoid MemoryError during local test execution
    lat = np.linspace(-90, -45, 45)
    lon = np.linspace(0, 359.5, 120)
    shape = (days, len(lat), len(lon))

    sic = np.random.uniform(0, 100, shape)
    era5 = {
        'u10': np.random.normal(0, 5, shape),
        'v10': np.random.normal(0, 5, shape),
        't2m': np.random.normal(260, 10, shape)
    }
    ocean = {
        'sst': np.random.normal(270, 2, shape),
        'mld': np.random.normal(50, 10, shape)
    }

    print('Initializing and training Ice-kNN-South model...')
    model = IceKNNSouthModel(k_neighbors=5, n_components=10)
    model.fit(sic, era5, ocean, dates, lat, lon)

    model_path = 'models/ice_knn_south_model.pkl'
    model.save(model_path)

    print('Running 90-day test inference...')
    init_date = '2019-12-31'
    init_sic = sic[-1]
    init_era5 = {k: v[-1] for k, v in era5.items()}
    init_ocean = {k: v[-1] for k, v in ocean.items()}

    forecast = model.predict(init_date, init_sic, init_era5, init_ocean, lead_days=90)
    out_path = 'models/amip_forecast_sample.nc'
    model.export_amip_netcdf(forecast, out_path)
    print('Done!')

