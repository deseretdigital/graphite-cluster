#!/usr/bin/php
<?php
    
    /**
     * Check which server contains the largest version of a particular wisper
     * file and sync it to the rest if necessary.
     */
    
    // Show syntax if the command line was wrong
    if ($argc != 2) {
        showSyntax();
        exit;
    }

    // Set the filename and grab its key
    $file = $argv[1];
    echo "$file  ";
    $key = getKeyFromFile($file);
    $servers = getServersForKey($key);
    $result = syncHighestServer($servers, $file, $key);
    if ($result !== true) {
        echo "Rsync error!\n";
    }

    /**
     * Return a key from a filename.
     */
    function getKeyFromFile($file) {
        $search = array(
            '.wsp',
            '/opt/graphite/storage/whisper/'
        );
        // Strip the extension and the preamble 
        $key = str_replace($search, '', $file);
        // Replace slashes with dots
        $key = str_replace('/', '.', $key);
        // Return the key
        return $key;
    }


    /**
     * Find the servers used for a particular key
     */
    function getServersForKey($key) {
        $search = array (
            '(',
            ')',
            ' '
        );
        // Execute the python script
        $cmd = "python /opt/graphite/maintenance/graphite-router.py -k $key";
        exec($cmd, $lines);
        // Get rid of the first line, it's junk
        array_shift($lines);
        // Loop through the lines
        foreach ($lines as $line) {
            // Strip stuff from the result to turn it into CSV data
            $line = str_replace($search, '', $line);
            // Turn the CSV into an array
            $fields = str_getcsv($line, ',', '\'');
            // Add the IP to the servers array
            $servers[] = $fields[0];
        }
        // Return the list
        return $servers;
    }


    function syncHighestServer($servers, $file, $key) {
        $result = true;
        // Get all the server totals
        $totals = getAllServerTotals($servers, $key);
        // Find the highest total from the array of totals
        $highest = max($totals);
        // Get the first IP with the high value
        foreach ($totals as $server => $total) {
            if ($total == $highest) {
                $highestServer = $server;
                continue;
            }
        }
        // Find the local IP address
        $localhost = gethostbyname(trim(`hostname`));
        // If this server is supposed to have this value
        if (in_array($localhost, $servers)) {
            // If this server has less than the highest server
            if ($totals[$localhost] < $highest) {
                echo "[synced]\n";
                // Sync the highest server here
                $result = syncFromServer($highestServer, $file);
            } else {
                echo "[ok]\n";
            }
        } else {
            echo "[orphan]\n";
            // TODO: Clean up a key that doesn't belong
            // The key isn't supposed to be on this server
            $result = true;
        }
        return $result;
    }


    function getServerTotal($server, $key) {
        // Grab the data from this server for this key
        $json = file_get_contents("http://{$server}:7001/render/?target={$key}&from=20100101&format=json");
        $data = json_decode($json, true);
        // Loop through the data
        $total = 0;
        foreach ($data[0]['datapoints'] as $point) {
            $total = $total + $point[0];
        }
        return $total;
    }


    function getAllServerTotals($servers, $key) {
        // Loop through the servers
        foreach ($servers as $server) {
            // Grab the total
            $sum = getServerTotal($server, $key);
            // Set an array of servers
            $totals[$server] = $sum;
        }
        return $totals;
    }


    function syncFromServer($from, $file) {
        // Strip the initial part of the path
        $whisperPath = str_replace('/opt/graphite/storage/whisper/', '', $file);
        $cmd = "rsync -avz $file rsync://{$from}/$whisperPath 2> /dev/null";
        // Execute the rsync command
        exec($cmd, $output, $result);
        // If the rsync was successful
        if ($result == 0) {
            $return = true;
        } else {
            $return = false;
        };
        // Return the result
        return $return;
    }

    function showSyntax() {
        echo 'walker.php <whisper_file>' . "\n";
    }

?>
