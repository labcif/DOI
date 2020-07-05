# Run the tests

In order to run the tests, perform one of this commands in root directory of doi project.

Run all tests:

`python -m unittest discover -s tests -b`

Run all unit tests:

`python -m unittest discover -s tests.unit -b`

Run all integration tests:

`python -m unittest discover -s tests.integration -b`

Run specific tests:

`python -m unittest tests.unit.test_detections_handler`

`python -m unittest tests.unit.test_detections_handler.TestDrawDetections`

`python -m unittest tests.unit.test_detections_handler.TestDrawDetections.test_not_draw_detections_when_disabled`


# Get code coverage

In order to get code coverage, run the command:

`pip install coverage`

Then, to run the tests and analyse code coverage, run the command:

`coverage run -m unittest discover -s tests -b`

A `.coverage` file is generated. Then, to see the report in the command line, run the command:

`coverage report`

To generate a nice HTML page for the report, run the command:

`coverage html`

The report HTML will be created on `htmlcov/index.html`.