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
                "notConnected"

        job

            { "id": (job-id)
            , "name": (job-name)
            , "state": (job-state)
            , "conclusion": (job-conclusion)
            , "currentstep": (job-step)
            }

        job-conclusion :: (string)

            How did the job conclude?
            four conclusions are defined:

                null (meaning not concluded)
                "ENDED"
                "FAILED"
                "CANCELED"

        job-id :: (number)

            A job identifier.

        job-name :: (string)

            A job name, human-readable.

        job-state :: (string)

            A job's state.
            There are three states defined:

                "PENDING"
                "RUNNING"
                "STOPPED"

        job-step

            { "name": (job-step-name)
            , "progress": (number)
            }

        job-step-name :: (string)

            The name of a job step, e.g "slicing", "printing".

        material-name :: (string)

            A material name.

        preprocessors

            [ (preprocessor-name)
            , ...
            ]

        preprocessor-name :: (string)

            A preprocessor name.

        printer

            { "profilename":       (profile-name)
            , "displayname":       (string)
            , "uniquename":        (printer-unique-name)
            , "printertype":       (string)
            , "canprint":          (bool)
            , "canprinttofile":    (bool)
            , "hasheatedplatform": (bool)
            , "numberoftoolheads": (number)
            , "connectionstatus":  (connection-status)
            , "temperature":       (tool-temperatures)
            }

        printer-unique-name :: (string)

            A unique name to identify a unique printer.

        profile-name :: (string)

            A profile name.

        rate :: (number)

            A travel rate.

        slicer-name :: (string)

            A slicer name.

        slicer-settings :: (string)

            A slicer settings object.

                { 'slicer':               (slicer-name)
                , 'extruder':             (extruder-name)
                , 'raft':                 (bool)
                , 'support':              (bool)
                , 'infill':               (number)
                , 'layer_height':         (number)
                , 'shells':               (number)
                , 'extruder_temperature': (temperature)
                , 'platform_temperature': (temperature)
                , 'print_speed':          (rate)
                , 'travel_speed':         (rate)
                }

        temperature :: (number)

            A temperature.

        tool-temperatures :: (string)

            A list of temperatures for all toolheads and heated build platforms on the printer.

                { "tools" :
                    { (tool-name) : 
                        (temperature)
                    , ...
                    }
                , "heated_platforms" :
                    { (tool-name) : 
                        (temperature)
                    , ...
                    }
                }

        tool-name :: (string)

            The name of a tool or heated build platform on the printer. These are ordinarily numbers represented as strings.

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

                { "uniquename":      (printer-unique-name)
                , "inputpath":       (absolute-file-path)
                , "preprocessor":    (preprocessors)
                , "skip_start_end":  (bool)
                , "archive_lvl":     (archive-level)
                , "archive_dir:"     (absolute-directory-path)
                , "slicer_settings": (slicer-settings)
                , "material":        (material-name)
                }

            result

                (job)

        printtofile

            This method creates and starts a print-to-file job.

            The "printername" field name and type should be changed to "profilename" and (profile-name).

            params

                { "profilename":     (profile-name)
                , "inputpath":       (absolute-file-path)
                , "outputpath":      (absolute-file-path)
                , "preprocessor":    (preprocessors)
                , "skip_start_end":  (bool)
                , "archive_lvl":     (archive-level)
                , "archive_dir:"     (absolute-directory-path)
                , "slicer_settings": (slicer-settings)
                , "material":        (material-name)
                }

            result

                (job)

        slice

            This method creates and starts a slice job.

            params

                { "profilename":     (profile-name)
                , "inputpath":       (absolute-file-path)
                , "outputpath":      (absolute-file-path)
                , "preprocessor":    (preprocessors)
                , "skip_start_end":  (bool)
                , "archive_lvl":     (archive-level)
                , "archive_dir:"     (absolute-directory-path)
                , "slicer_settings": (slicer-settings)
                , "material":        (material-name)
                }

            result

                (job)

        canceljob

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

                { "uniquename": (printer-unique-name)
                }

            result

                (printer)

        getprinters

            This method returns the list of printers.

            params

                {
                }

            result

                [ (printer)
                , ...
                ]

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

                [ (job)
                , ...
                ]

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

                (printer)

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

        jobremoved

            The server invokes this method after a job finishes.

            params

                (job)
                
<!-- vim:set ai et fenc=utf-8 ff=unix sw=4 syntax=markdown ts=4: -->
