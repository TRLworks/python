#!/bin/bash
#
#script to disable the jenkins job
#
#
#
for m in `cat /Users/jselvakumar/Jenkins_job/jobs_name_ms_orange_1`
do
echo `java -jar /Users/jselvakumar/Downloads/jenkins-cli.jar -s http://mic-st-build01.msorange.dom:8080 disable-job $m`

done

exit0

