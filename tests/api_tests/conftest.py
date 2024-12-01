import logging
import json
import time

from threading import Thread

from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest


LOGGER = logging.getLogger("scyllaapiserver")

class ScyllaAPIBasicRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/api-doc":
            content = json.dumps(self.api_doc()).encode(encoding="utf-8")
        elif self.path == "/api-doc/system/":
            content = json.dumps(self.system()).encode(encoding="utf-8")
        elif self.path == "/api-doc/error_injection/":
            content = json.dumps(self.error_injection()).encode(encoding="utf-8")
        elif self.path == "/api-doc/compaction_manager/":
            content = json.dumps(self.compaction_manager()).encode(encoding="utf-8")
        elif self.path == "/v2":
            content = json.dumps(self.v2()).encode(encoding="utf-8")
        else:
            content = json.dumps(f"""{{"URL": "{self.command}", "method": "{self.path}"}}""").encode(encoding="utf-8")

        self._send_response(content)

    def _send_response(self, content):
        self.send_response(200)
        self.send_header("Content-Length", f"{len(content)}")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(content)

    def api_doc(self):
        json_resp = json.loads(
        """{
        "apiVersion": "0.0.1", "swaggerVersion": "1.2", 
        "apis": [
            {"path": "/system", "description": "The system related API"},
            {"path": "/compaction_manager", "description": "The Compaction manager API"},
            {"path": "/error_injection", "description": "The error injection API"}
        ]}"""
        )
        return json_resp

    def system(self):
        return json.loads("""{
   "apiVersion":"0.0.1",
   "swaggerVersion":"1.2",
   "basePath":"http://127.0.0.1:10000",
   "resourcePath":"/system",
   "produces":[
      "application/json"
   ],
   "apis":[
      {
         "path":"/system/logger",
         "operations":[
            {
               "method":"GET",
               "summary":"Get all logger names",
               "type":"array",
               "items":{
                  "type":"string"
               },
               "nickname":"get_all_logger_names",
               "produces":[
                  "application/json"
               ],
               "parameters":[
               ]
            },
            {
               "method":"POST",
               "summary":"Set all logger level",
               "type":"void",
               "nickname":"set_all_logger_level",
               "produces":[
                  "application/json"
               ],
               "parameters":[
                  {
                     "name":"level",
                     "description":"The new log level",
                     "required":true,
                     "allowMultiple":false,
                     "type":"string",
                     "enum":[
                        "error",
                        "warn",
                        "info",
                        "debug",
                        "trace"
                     ],
                     "paramType":"query"
                  }
               ]
            }
         ]
      },
      {
         "path":"/system/drop_sstable_caches",
         "operations":[
            {
               "method":"POST",
               "summary":"Drop in-memory caches for data which is in sstables",
               "type":"void",
               "nickname":"drop_sstable_caches",
               "produces":[
                  "application/json"
               ],
               "parameters":[
               ]
            }
         ]
      },
      {
         "path":"/system/uptime_ms",
         "operations":[
            {
               "method":"GET",
               "summary":"Get system uptime, in milliseconds",
               "type":"long",
               "nickname":"get_system_uptime",
               "produces":[
                  "application/json"
               ],
               "parameters":[]
            }
         ]
      },
      {
         "path":"/system/logger/{name}",
         "operations":[
            {
               "method":"GET",
               "summary":"Get logger level",
               "type":"string",
               "nickname":"get_logger_level",
               "produces":[
                  "application/json"
               ],
               "parameters":[
                  {
                     "name":"name",
                     "description":"The logger to query about",
                     "required":true,
                     "allowMultiple":false,
                     "type":"string",
                     "paramType":"path"
                  }
               ]
            },
            {
               "method":"POST",
               "summary":"Set logger level",
               "type":"void",
               "nickname":"set_logger_level",
               "produces":[
                  "application/json"
               ],
               "parameters":[
                  {
                     "name":"name",
                     "description":"The logger to query about",
                     "required":true,
                     "allowMultiple":false,
                     "type":"string",
                     "paramType":"path"
                  },
                  {
                     "name":"level",
                     "description":"The new log level",
                     "required":true,
                     "allowMultiple":false,
                     "type":"string",
                     "enum":[
                        "error",
                        "warn",
                        "info",
                        "debug",
                        "trace"
                     ],
                     "paramType":"query"
                  }
               ]
            }
         ]
      }
   ]
}
""")

    def error_injection(self):
        return json.loads("""{
   "apiVersion":"0.0.1",
   "swaggerVersion":"1.2",
   "basePath":"http://127.0.0.1:10000",
   "resourcePath":"/error_injection",
   "produces":[
      "application/json"
   ],
   "apis":[
      {
         "path":"/v2/error_injection/injection/{injection}",
         "operations":[
            {
               "method":"POST",
               "summary":"Activate an injection that triggers an error in code",
               "type":"void",
               "nickname":"enable_injection",
               "produces":[
                  "application/json"
               ],
               "parameters":[
                  {
                     "name":"injection",
                     "description":"injection name, should correspond to an injection added in code",
                     "required":true,
                     "allowMultiple":false,
                     "type":"string",
                     "paramType":"path"
                  },
                  {
                     "name":"one_shot",
                     "description":"boolean flag indicating whether the injection should be enabled to trigger only once",
                     "required":false,
                     "allowMultiple":false,
                     "type":"boolean",
                     "paramType":"query"
                  }
               ]
            },
            {
               "method":"DELETE",
               "summary":"Deactivate an injection previously activated by the API",
               "type":"void",
               "nickname":"disable_injection",
               "produces":[
                  "application/json"
               ],
               "parameters":[
                  {
                     "name":"injection",
                     "description":"injection name",
                     "required":true,
                     "allowMultiple":false,
                     "type":"string",
                     "paramType":"path"
                  }
               ]
            }
         ]
      },
      {
         "path":"/v2/error_injection/injection",
         "operations":[
            {
               "method":"GET",
               "summary":"List all enabled injections on all shards, i.e. injections that will trigger an error in the code",
               "type":"array",
               "items":{
                  "type":"string"
               },
               "nickname":"get_enabled_injections_on_all",
               "produces":[
                  "application/json"
               ],
               "parameters":[]
            },
            {
               "method":"DELETE",
               "summary":"Deactivate all injections previously activated on all shards by the API",
               "type":"void",
               "nickname":"disable_on_all",
               "produces":[
                  "application/json"
               ],
               "parameters":[]
            }
         ]
      }
   ]
}
""")

    def compaction_manager(self):
            return json.loads("""{
   "apiVersion":"0.0.1",
   "swaggerVersion":"1.2",
   "basePath":"http://127.0.0.1:10000",
   "resourcePath":"/compaction_manager",
   "produces":[
      "application/json"
   ],
   "apis":[
      {
         "path":"/compaction_manager/compactions",
         "operations":[
            {
               "method":"GET",
               "summary":"get List of running compactions",
               "type":"array",
               "items":{
                  "type":"summary"
               },
               "nickname":"get_compactions",
               "produces":[
                  "application/json"
               ],
               "parameters":[
               ]
            }
         ]
      },
      {
         "path":"/compaction_manager/compaction_history",
         "operations":[
            {
               "method":"GET",
               "summary":"get List of the compaction history",
               "type":"array",
               "items":{
                  "type":"history"
               },
               "nickname":"get_compaction_history",
               "produces":[
                  "application/json"
               ],
               "parameters":[
               ]
            }
         ]
      },
      {
         "path":"/compaction_manager/compaction_info",
         "operations":[
            {
               "method":"GET",
               "summary":"get a list of all active compaction info",
               "type":"array",
               "items":{
                  "type":"compaction_info"
               },
               "nickname":"get_compaction_info",
               "produces":[
                  "application/json"
               ],
               "parameters":[
               ]
            }
         ]
      },
      {
         "path":"/compaction_manager/force_user_defined_compaction",
         "operations":[
            {
               "method":"POST",
               "summary":"Triggers the compaction of user specified sstables. You can specify files from various keyspaces and columnfamilies. If you do so, user defined compaction is performed several times to the groups of files in the same keyspace/columnfamily. must contain keyspace and columnfamily name in path(for 2.1+) or file name itself.",
               "type":"void",
               "nickname":"force_user_defined_compaction",
               "produces":[
                  "application/json"
               ],
               "parameters":[
                  {
                     "name":"data_files",
                     "description":"a comma separated list of sstable file to compact. must contain keyspace and columnfamily name in path(for 2.1+) or file name itself",
                     "required":true,
                     "allowMultiple":false,
                     "type":"string",
                     "paramType":"query"
                  }
               ]
            }
         ]
      },
      {
         "path":"/compaction_manager/stop_compaction",
         "operations":[
            {
               "method":"POST",
               "summary":"Stop all running compaction-like tasks having the provided type",
               "type":"void",
               "nickname":"stop_compaction",
               "produces":[
                  "application/json"
               ],
               "parameters":[
                  {
                     "name":"type",
                     "description":"the type of compaction to stop. Can be one of: - COMPACTION - VALIDATION - CLEANUP - SCRUB - INDEX_BUILD",
                     "required":true,
                     "allowMultiple":false,
                     "type":"string",
                     "paramType":"query"
                  }
               ]
            }
         ]
      },
      {
      "path": "/compaction_manager/metrics/pending_tasks",
      "operations": [
        {
          "method": "GET",
          "summary": "Get pending tasks",
          "type": "long",
          "nickname": "get_pending_tasks",
          "produces": [
            "application/json"
          ],
          "parameters": []
        }
      ]
    },
    {
      "path": "/compaction_manager/metrics/pending_tasks_by_table",
      "operations": [
        {
          "method": "GET",
          "summary": "Get pending tasks by table name",
          "type": "array",
          "items": {
              "type": "pending_compaction"
           },
          "nickname": "get_pending_tasks_by_table",
          "produces": [
            "application/json"
          ],
          "parameters": []
        }
      ]
    },
    {
      "path": "/compaction_manager/metrics/completed_tasks",
      "operations": [
        {
          "method": "GET",
          "summary": "Get completed tasks",
          "type": "long",
          "nickname": "get_completed_tasks",
          "produces": [
            "application/json"
          ],
          "parameters": []
        }
      ]
    },
    {
      "path": "/compaction_manager/metrics/total_compactions_completed",
      "operations": [
        {
          "method": "GET",
          "summary": "Get total compactions completed",
          "type": "long",
          "nickname": "get_total_compactions_completed",
          "produces": [
            "application/json"
          ],
          "parameters": []
        }
      ]
    },
    {
      "path": "/compaction_manager/metrics/bytes_compacted",
      "operations": [
        {
          "method": "GET",
          "summary": "Get bytes compacted",
          "type": "long",
          "nickname": "get_bytes_compacted",
          "produces": [
            "application/json"
          ],
          "parameters": []
        }
      ]
    }
   ],
   "models":{
      "row_merged":{
         "id":"row_merged",
         "description":"A row merged information",
         "properties":{
            "key":{
               "type": "long",
               "description":"The number of sstable"
            },
            "value":{
               "type":"long",
               "description":"The number or row compacted"
            }
         }
      },
      "compaction_info" :{
          "id": "compaction_info",
          "description":"A key value mapping",
          "properties":{
            "operation_type":{
               "type":"string",
               "description":"The operation type"
            },
            "completed":{
               "type":"long",
               "description":"The current completed"
            },
            "total":{
               "type":"long",
               "description":"The total to compact"
            },
            "unit":{
               "type":"string",
               "description":"The compacted unit"
            }
          }
      },
      "summary":{
         "id":"summary",
         "description":"A compaction summary object",
         "properties":{
            "id":{
               "type":"string",
               "description":"The UUID"
            },
            "ks":{
               "type":"string",
               "description":"The keyspace name"
            },
            "cf":{
               "type":"string",
               "description":"The column family name"
            },
            "completed":{
               "type":"long",
               "description":"The number of units completed"
            },
            "total":{
               "type":"long",
               "description":"The total number of units"
            },
            "task_type":{
               "type":"string",
               "description":"The task compaction type"
            },
            "unit":{
               "type":"string",
               "description":"The units being used"
            }
         }
      },
      "pending_compaction": {
        "id": "pending_compaction",
        "properties": {
            "cf": {
               "type": "string",
               "description": "The column family name"
            },
            "ks": {
               "type":"string",
               "description": "The keyspace name"
            },
            "task": {
               "type":"long",
               "description": "The number of pending tasks"
            }
        }
      },
      "history": {
      "id":"history",
      "description":"Compaction history information",
      "properties":{
            "id":{
               "type":"string",
               "description":"The UUID"
            },
            "cf":{
               "type":"string",
               "description":"The column family name"
            },
            "ks":{
               "type":"string",
               "description":"The keyspace name"
            },
            "compacted_at":{
               "type":"long",
               "description":"The time of compaction"
            },
            "bytes_in":{
               "type":"long",
               "description":"Bytes in"
            },
            "bytes_out":{
               "type":"long",
               "description":"Bytes out"
            },
            "rows_merged":{
               "type":"array",
               "items":{
                  "type":"row_merged"
               },
               "description":"The merged rows"
            }
        }
      }
   }
}""")

    def v2(self):
        json_resp = json.loads("""{
  "swagger": "2.0",
  "info": {
    "version": "1.0.0",
    "title": "Scylla API",
    "description": "The scylla API version 2.0",
    "termsOfService": "http://www.scylladb.com/tos/",
    "contact": {
      "name": "Scylla Team",
      "email": "info@scylladb.com",
      "url": "http://scylladb.com"
    },
    "license": {
      "name": "AGPL",
      "url": "https://github.com/scylladb/scylla/blob/master/LICENSE.AGPL"
    }
  },
  "host": "localhost:10000",
  "basePath": "/",
  "schemes": [
    "http"
  ],
  "consumes": [
    "application/json"
  ],
  "produces": [
    "application/json"
  ],
  "paths": {
    "/v2/metrics-config/":{
        "get":{
            "description":"Return the metrics layer configuration",
            "operationId":"get_metrics_config",
            "produces":[
                "application/json"
            ],
            "tags":[
                "metrics"
            ],
            "parameters":[
            ],
            "responses":{
                "200":{
                "schema": {
                    "type":"array",
                    "items":{
                        "$ref":"#/definitions/metrics_config",
                        "description":"metrics Config value"
                    }
                    }
                },
                "default":{
                    "description":"unexpected error",
                    "schema":{
                        "$ref":"#/definitions/ErrorModel"
                    }
                }
            }
        },
        "post": {
             "description":"Set the metrics layer relabel configuration",
            "operationId":"set_metrics_config",
            "produces":[
                "application/json"
            ],
            "tags":[
                "metrics"
            ],
            "parameters":[
               {
                "in":"body",
                "name":"conf",
                "description":"An array of relabel_config objects",
                "schema": {
                    "type":"array",
                    "items":{
                        "$ref":"#/definitions/metrics_config",
                        "description":"metrics Config value"
                    }
                }
               }
            ],
            "responses":{
                "200":{
                    "description": "OK"
                },
                "default":{
                    "description":"unexpected error",
                    "schema":{
                        "$ref":"#/definitions/ErrorModel"
                    }
                }
            }
        }
    },
    "/v2/config/background_writer_scheduling_quota": {
      "get": {
        "description": "max cpu usage ratio (between 0 and 1) for compaction process. Not intended for setting in normal operations. Setting it to 1 or higher will disable it, recommended operational setting is 0.5.",
        "operationId": "find_config_background_writer_scheduling_quota",
        "produces": [
          "application/json"
        ],
        "tags": [
          "config"
        ],
        "parameters": [],
        "responses": {
          "200": {
            "description": "Config value",
            "schema": {
              "type": "double"
            }
          },
          "default": {
            "description": "unexpected error",
            "schema": {
              "$ref": "#/definitions/ErrorModel"
            }
          }
        }
      }
    },
    "/v2/config/log_to_syslog": {
      "get": {
        "description": "Send log output to syslog",
        "operationId": "find_config_log_to_syslog",
        "produces": [
          "application/json"
        ],
        "tags": [
          "config"
        ],
        "parameters": [],
        "responses": {
          "200": {
            "description": "Config value",
            "schema": {
              "type": "bool"
            }
          },
          "default": {
            "description": "unexpected error",
            "schema": {
              "$ref": "#/definitions/ErrorModel"
            }
          }
        }
      }
    }
  },
  "definitions": {
    "metrics_config": {
      "id": "metrics_config",
      "summary": "An entry in the metrics configuration",
      "properties": {
        "source_labels": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "The source labels, a match is based on concatenation of the labels"
        },
        "action": {
          "type": "string",
          "description": "The action to perform on match",
          "enum": [
            "skip_when_empty",
            "report_when_empty",
            "replace",
            "keep",
            "drop",
            "drop_label"
          ]
        },
        "target_label": {
          "type": "string",
          "description": "The application state version"
        },
        "replacement": {
          "type": "string",
          "description": "The replacement string to use when replacing a value"
        },
        "regex": {
          "type": "string",
          "description": "The regex string to use when replacing a value"
        },
        "separator": {
          "type": "string",
          "description": "The separator string to use when concatenating the labels"
        }
      }
    }
  }
}"""
        )
        return json_resp


class ScyllaApiServer:
    def __init__(self, port):
        self.host = "localhost"
        self.port = port
        self.httpd = None

    def run_server(self):
        LOGGER.info("Start server")
        self.httpd = HTTPServer((self.host, self.port), ScyllaAPIBasicRequestHandler)
        self.httpd.serve_forever()

    def stop_server(self):
        LOGGER.info("Shutdown server")
        if self.httpd:
            self.httpd.shutdown()


@pytest.fixture(scope="module")
def api_server():
    httpd = ScyllaApiServer(port=10101)
    httpd_thread = Thread(target=httpd.run_server, name="scylla http api sever", daemon=True)
    httpd_thread.start()
    time.sleep(2)
    yield httpd
    httpd.stop_server()
