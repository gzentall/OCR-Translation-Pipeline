import React, { useState, useEffect } from 'react';
import {
  Autocomplete,
  TextField,
  CircularProgress,
  Box,
  Typography,
} from '@mui/material';
import { LocationOn as LocationIcon } from '@mui/icons-material';

interface Location {
  city: string;
  state?: string;
  country: string;
  latitude: number;
  longitude: number;
  display_name: string;
}

interface LocationAutocompleteProps {
  label: string;
  value: Location | null;
  onChange: (location: Location | null) => void;
  placeholder?: string;
}

const LocationAutocomplete: React.FC<LocationAutocompleteProps> = ({
  label,
  value,
  onChange,
  placeholder = "Start typing a city name...",
}) => {
  const [open, setOpen] = useState(false);
  const [options, setOptions] = useState<Location[]>([]);
  const [loading, setLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');

  useEffect(() => {
    if (inputValue.length < 3) {
      setOptions([]);
      return;
    }

    const searchLocations = async () => {
      setLoading(true);
      try {
        // Using Geoapify Places Autocomplete (Option #2)
        const API_KEY = process.env.REACT_APP_GEOAPIFY_API_KEY || 'your_api_key_here';
        
        const url = `https://api.geoapify.com/v1/geocode/autocomplete?` +
          `text=${encodeURIComponent(inputValue)}` +
          `&type=city` +
          `&apiKey=${API_KEY}` +
          `&limit=8`;
        
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        const locations: Location[] = data.features
          .filter((feature: any) => feature.properties.city)
          .map((feature: any) => ({
            display_name: feature.properties.formatted,
            city: feature.properties.city,
            state: feature.properties.state,
            country: feature.properties.country,
            latitude: feature.properties.lat,
            longitude: feature.properties.lon,
          }));

        setOptions(locations);
      } catch (error) {
        console.error('Geocoding error:', error);
        setOptions([]);
      } finally {
        setLoading(false);
      }
    };

    // Debounce: wait 500ms after user stops typing
    const timeoutId = setTimeout(searchLocations, 500);
    return () => clearTimeout(timeoutId);
  }, [inputValue]);

  return (
    <Autocomplete
        open={open}
        onOpen={() => setOpen(true)}
        onClose={() => setOpen(false)}
        options={options}
        loading={loading}
        getOptionLabel={(option) => option.display_name}
        isOptionEqualToValue={(option, value) => 
          option.latitude === value.latitude && option.longitude === value.longitude
        }
      onInputChange={(event, newInputValue) => {
        setInputValue(newInputValue);
      }}
        onChange={(event, value) => {
          onChange(value);
        }}
        value={value}
        renderInput={(params) => (
          <TextField
            {...params}
            label={label}
            placeholder={placeholder}
            InputProps={{
              ...params.InputProps,
              startAdornment: <LocationIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              endAdornment: (
                <>
                  {loading ? <CircularProgress color="inherit" size={20} /> : null}
                  {params.InputProps.endAdornment}
                </>
              ),
            }}
          />
        )}
        renderOption={(props, option) => (
          <Box component="li" {...props}>
            <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
              <LocationIcon sx={{ mr: 1, color: 'text.secondary', fontSize: 20 }} />
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {option.city}
                  {option.state && `, ${option.state}`}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {option.country}
                </Typography>
              </Box>
            </Box>
          </Box>
        )}
      />
  );
};

export default LocationAutocomplete;
