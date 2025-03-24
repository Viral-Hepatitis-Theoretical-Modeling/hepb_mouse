# This file is part of the HepB Model
#
# HepCB Enum classes
# 
# Uses the aenum 'advanced enumerations' library to define multi value
#  tuples for each, to support compact logging.
#

from enum import Enum

class Status(Enum):
    SUSCEPTIBLE = "SUSCEPTIBLE"
    ECLIPSED = "ECLIPSED"
    INFECTED = "INFECTED"

class LogType(Enum):

    ACTIVATED = "ACTIVATED"
    EXPOSED   = "EXPOSED"
    INFECTED = "INFECTED"
    INFECTIOUS = "INFECTIOUS"
    CHRONIC = "CHRONIC"
    RECOVERED = "RECOVERED"
    DEACTIVATED = "DEACTIVATED"
    INFO = "INFO"
    STATUS = "STATUS"
    STARTED_TREATMENT = "STARTED_TREATMENT"
    STARTED_OPIOID_TREATMENT = "STARTED_OPIOID_TREATMENT"
    STOPPED_OPIOID_TREATMENT = "STOPPED_OPIOID_TREATMENT"
    CURED = "CURED"
    REGULAR_STATUS = "REGULAR_STATUS"
    FAILED_TREATMENT = "FAILED_TREATMENT"
    HCVRNA_TEST = "HCVRNA_TEST"

