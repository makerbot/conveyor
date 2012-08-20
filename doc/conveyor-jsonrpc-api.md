This is a preliminary API specification.
It is unstable and subject to change.

This document is not currently complete.

The server is the conveyor deamon.
The client is either the conveyor command-line client or any other application that connects to the conveyor daemon (i.e., by using conveyor's C++ API).

The server and client are actually peers and they invoke methods on eachother asynchronously.
However, the server never expects a response when it invokes a method on the client; it always sends JSON-RPC notifications to the client.

Common Types

    Core JSON Types

        array
        bool
        number
        object
        string

    conveyor Types

        These types are aliases of the core JSON types but with additional semantic meaning.

        absolute-directory-path :: (string)

            An absolute directory path.

        absolute-file-path :: (string)

            An absolute file path.

        archive-level :: (string)

            An archive level.
            Two archive levels are defined:

                null
                "all"

        connection-status :: (string)

            The connection status.
            There are two connection statuses defined:

                "connected"
                "disconnected"

        extruder-profile

            { "firstLayerExtrusionProfile": (extrusion-profile-name)
            , "insetsExtrusionProfile":     (extrusion-profile-name)
            , "infillsExtrusionProfile":    (extrusion-profile-name)
            , "outlineExtrusionProfile":    (extrusion-profile-name)
            }

        extruder-profile-name :: (string)

            An extruder profile name.

        extrusion-profile

            { "temperature": (temperature)
            , "feedrate":    (rate)
            }

        extrusion-profile-name :: (string)

            An extrusion profile name.

        job

            { "id": (job-id)
            }

        job-id :: (number)

            A job identifier.

        preprocessor-name :: (string)

            A preprocessor name.

        printer

            { "printername":       (printer-name)
            , "displayName":       (string)
            , "uniqueName":        (string)
            , "printerType":       (string)
            , "canPrint":          (bool)
            , "canPrintToFile":    (bool)
            , "hasHeatedPlatform": (bool)
            , "numberOfToolheads": (number)
            , "connectionStatus":  (connection-status)
            }

        printer-name :: (string)

            A printer name.

        profile-name :: (string)

            A profile name.

        rate :: (number)

            A travel rate.

        slicer-name :: (string)

            A slicer name.

        slicer-settings :: (string)

            A slicer settings object.

                { (slicer-name):
                    { "doRaft":              (bool)
                    , "doSupport":           (bool)
                    , "extruder":
                        { "defaultExtruder": (number)
                        }
                    , "extruderProfiles":
                        [ (extruder-profile)
                        , ...
                        ]
                    , "extrusionProfiles":
                        { (extrusion-profile-name):
                            (extrusion-profile)
                        , ...
                        }
                    , "infillDensity":       (number)
                    , "layerHeight":         (number)
                    , "numberOfShells":      (number)
                    , "platformTemperature": (temperature)
                    , "rapidMoveFeedRateXY": (rate)
                    }
                , "slicer":
                    { "maxVersion":          (version)
                    , "minVersion":          (version)
                    , "slicerName":          (slicer-name)
                    }
                }

        temperature :: (number)

            A temperature.

        version :: (string)

            A version.

Server

    Core API

        hello

            This method *MUST* be called exactly once when a client first connects to conveyor.
            Clients *MUST* not invoke any other methods before calling hello.
            Clients *MUST* not invoke hello more than once.

            params

                {
                }

            result

                "world"

        print

            This method creates and starts a print job.

            params

                { "printername":     (printer-name)
                , "inputpath":       (absolute-file-path)
                , "preprocessor":    (preprocessor-name)
                , "skip_start_end":  (bool)
                , "archive_lvl":     (archive-level)
                , "archive_dir:"     (absolute-directory-path)
                , "slicer_settings": (slicer-settings)
                }

            result

                (job)

        printtofile

            This method creates and starts a print-to-file job.

            The "printername" field name and type should be changed to "profilename" and (profile-name).

            params

                { "printername":     (string)
                , "inputpath":       (absolute-file-path)
                , "outputpath":      (absolute-file-path)
                , "preprocessor":    (string)
                , "skip_start_end":  (bool)
                , "archive_lvl":     (archive-level)
                , "archive_dir:"     (absolute-directory-path)
                , "slicer_settings": (slicer-settings)
                }

            result

                (job)

        slice

            This method creates and starts a slice job.

            The "printername" field name and type should be changed to "profilename" and (profile-name).

            params

                { "printername":     (printer-name)
                , "inputpath":       (absolute-file-path)
                , "outputpath":      (absolute-file-path)
                , "preprocessor":    (string)
                , "skip_start_end":  (bool)
                , "archive_lvl":     (archive-level)
                , "archive_dir:"     (absolute-directory-path)
                , "slicer_settings": (slicer-settings)
                }

            result

                (job)

        cancel

            This method schedules a job for cancellation.
            The job may or may not be canceled when this method returns.

            params

                { "id": (job-id)
                }

            result

                null

        getprinter

            This method returns the details for a printer.

            params

                { "printername": (printer-name)
                }

            result

                (printer)

        getprinters

            This method returns the list of printers.

            params

                {
                }

            result

                [(printer), ...]

        getjob

            This method returns the details for a job.

            params

                { "id": (job-id)
                }

            result

                (job)

        getjobs

            This method returns the list of jobs.

            params

                {
                }

            result

                [(job), ...]

        dir

        printer\_query

        printer\_scan

Client

    The server only ever makes JSON-RPC notification calls to the client.
    It never expects a response.
    The result for any of the client API methods is 'null'.

    Core API

        printeradded

            The server invokes this method when a new printer is connected.

            params

                (printer)

        printerremoved

            The server invokes this method when a printer is disconnected.

            params

                { "printername": (printer-name)
                }

        printerchanged

            The server invokes this method when a printer changes.

            params

                (printer)

        jobadded

            The server invokes this method whenever a new job is added.

            params

                (job)

        jobchanged

            The server invokes this method whenever a job changes.

            params

                (job)

<!-- vim:set ai et fenc=utf-8 ff=unix sw=4 syntax=markdown ts=4: -->
