import across.sdk.v1 as sdk
from across.client import Client
try:
    from .footprint_util import project_footprint
except ImportError:
    from footprint_util import project_footprint  # type: ignore

class PandoraACROSSScheduleHandler:
    def __init__(
        self,
        client: Client,
        observation_status: sdk.ObservationStatus,
        schedule_status: sdk.ScheduleStatus,
        schedule_fidelity: sdk.ScheduleFidelity,
        schedule_name: str,
    ):
        """Initialize ACROSS schedule context for Pandora observations.

        Args:
            client: Authenticated ACROSS client used for API calls.
            observation_status: Status assigned to each created observation.
            schedule_status: Status assigned to the created schedule.
            schedule_fidelity: Fidelity level describing schedule maturity.
            schedule_name: Human-readable schedule label used in naming.
        """
        self.client = client
        self.observation_status = observation_status
        self.schedule_status = schedule_status
        self.schedule_fidelity = schedule_fidelity
        self.schedule_name = schedule_name
        self.pandora_telescope = self.client.telescope.get_many(name="Pandora", include_footprints=True, include_filters=True)[0]

        visda = [inst for inst in self.pandora_telescope.instruments if inst.short_name == "VISDA"][0] # type: ignore
        nirda = [inst for inst in self.pandora_telescope.instruments if inst.short_name == "NIRDA"][0] # type: ignore

        self.instrument_config = {
            "VISDA": {
                "instrument": visda,
                "bandpass": sdk.WavelengthBandpass(
                    filter_name=visda.filters[0].name, # type: ignore
                    min=visda.filters[0].min_wavelength, # type: ignore
                    max=visda.filters[0].max_wavelength, # type: ignore
                    unit=sdk.WavelengthUnit.ANGSTROM
                ),
                "observation_type": sdk.ObservationType.IMAGING
            },
            "NIRDA": {
                "instrument": nirda,
                "bandpass": sdk.WavelengthBandpass(
                    filter_name=nirda.filters[0].name, # type: ignore
                    min=nirda.filters[0].min_wavelength, # type: ignore
                    max=nirda.filters[0].max_wavelength, # type: ignore
                    unit=sdk.WavelengthUnit.ANGSTROM
                ),
                "observation_type": sdk.ObservationType.SPECTROSCOPY
            },
        }

    def transform_observations_to_across(self, instrument_config: dict, observations: list[dict]) -> list[sdk.ObservationCreate]:
        """Transform parsed observation dictionaries into ACROSS models.

        The method maps sky coordinates, timing, and instrument metadata into
        SDK observation objects, and projects detector footprints onto the sky
        when footprint geometry is available.

        Args:
            instrument_config: Instrument-specific ACROSS configuration, with
                instrument object, bandpass, and observation type.
            observations: Parsed observation dictionaries from the XML schedule.

        Returns:
            A list of `sdk.ObservationCreate` objects ready for submission.
        """
        
        across_observations = []

        instrument: sdk.Instrument = instrument_config["instrument"]
        bandpass: sdk.WavelengthBandpass = instrument_config["bandpass"]
        observation_type: sdk.ObservationType = instrument_config["observation_type"]

        for obs in observations:
            footprint = None
            if instrument.footprints is not None:
                footprint = project_footprint(
                    footprint_points=instrument.footprints, # type: ignore
                    ra=obs["ra"],
                    dec=obs["dec"],
                    roll_angle=obs["roll"],
                )

            across_observations.append(
                sdk.ObservationCreate(
                    instrument_id=instrument.id,
                    object_name=obs["target"],
                    pointing_position=sdk.Coordinate(
                        ra=obs["ra"],
                        dec=obs["dec"],
                    ),
                    pointing_angle=obs["roll"],
                    date_range=sdk.DateRange(
                        begin=obs["start"],
                        end=obs["end"],
                    ),
                    external_observation_id=f"obs_{obs['visit_id']}_{obs['sequence_id']}",
                    type=observation_type,
                    status=self.observation_status,
                    exposure_time=obs["duration_seconds"],
                    bandpass=sdk.Bandpass(bandpass),
                    footprint=footprint,
                )
            )

        return across_observations
    
    def run(self, observations: list[dict]):
        """Build and submit a Pandora schedule to ACROSS.

        This method creates VISDA and NIRDA observations, computes the full
        schedule date range, generates a descriptive schedule name, and posts
        the schedule to the ACROSS API.

        Args:
            observations: Parsed observation dictionaries from the ingest step.

        Raises:
            sdk.ApiException: Raised for API failures other than conflict (409).
        """

        visda_observations = self.transform_observations_to_across(self.instrument_config["VISDA"], observations)
        nirda_observations = self.transform_observations_to_across(self.instrument_config["NIRDA"], observations)
        all_observations = visda_observations + nirda_observations

        begin = min(obs.date_range.begin for obs in all_observations)
        end = max(obs.date_range.end for obs in all_observations)

        begin_str = begin.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")

        name = f"PANDORA_{self.schedule_name}_{begin_str}_{end_str}"

        schedule = sdk.ScheduleCreate(
            telescope_id=self.pandora_telescope.id,
            observations=visda_observations + nirda_observations,
            date_range=sdk.DateRange(
                begin=begin,
                end=end,
            ),
            status=self.schedule_status,
            fidelity=self.schedule_fidelity,
            name=name,
        )

        try:
            self.client.schedule.post(schedule)
        except sdk.ApiException as err:
            if err.status == 409:
                print("Schedule already exists.", err.__dict__)
            else:
                raise err