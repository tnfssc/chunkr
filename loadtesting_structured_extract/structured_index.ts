import { Worker, isMainThread, workerData, parentPort } from "worker_threads";
import axios from "axios";
import FormData from "form-data";
import fs from "fs";
import dotenv from "dotenv";
import { createObjectCsvWriter } from "csv-writer";
import pLimit from "p-limit";
import { fileURLToPath } from "url";
import path from "path";
import { EventEmitter } from "events";
import { v4 as uuidv4 } from "uuid";
import { performance } from "perf_hooks";
import { Blob } from "buffer";

import {
  TaskResponse,
  AggregateResults,
  WorkerResult,
  FailureTypes,
  ModelConfig,
} from "../loadtesting/src/models";

dotenv.config();

const API_URL = process.env.API_URL as string;
const API_KEY = process.env.API_KEY as string;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

if (!API_KEY || !API_URL) {
  console.error("API_KEY or API_URL not found in environment variables");
  process.exit(1);
}

const eventEmitter = new EventEmitter();

const MAX_FILES_TO_PROCESS = 200;
const CONCURRENT_REQUESTS_PER_WORKER = 5;
const WORKERS_PER_CONFIG = 4;
const INPUT_FOLDER = path.join(__dirname, "..", "input");
const OUTPUT_FOLDER = path.join(
  __dirname,
  "..",
  "output_structured_extraction"
);
const RUN_ID = `${new Date().toISOString().replace(/[:.]/g, "-")}_${uuidv4().slice(0, 8)}`;
let RUN_FOLDER = path.join(OUTPUT_FOLDER, RUN_ID);

// Ensure output folders exist
[OUTPUT_FOLDER, RUN_FOLDER].forEach((folder) => {
  if (!fs.existsSync(folder)) {
    fs.mkdirSync(folder, { recursive: true });
  }
});

const MODEL_CONFIGS: (ModelConfig & { workers: number })[] = [
  {
    model: "HighQuality",
    segmentationStrategy: "Page",
    ocrStrategy: "Off",
    percentage: 100,
    workers: WORKERS_PER_CONFIG,
  },
];

const EXTRACTION_SCHEMA = {
  title: "Document Metadata",
  type: "object",
  properties: [
    {
      name: "title",
      title: "Document Title",
      type: "string",
      description: "The main title of the document",
      default: null,
    },
    {
      name: "author",
      title: "Author",
      type: "string",
      description: "The author(s) of the document",
      default: null,
    },
    {
      name: "date_published",
      title: "Date Published",
      type: "string",
      description: "The publication date of the document",
      default: null,
    },
    {
      name: "location",
      title: "Location",
      type: "string",
      description: "The location mentioned in the document",
      default: null,
    },
  ],
};

// Save configurations to a txt file
const configFilePath = path.join(RUN_FOLDER, "config.txt");
const configData = {
  MODEL_CONFIGS,
  MAX_FILES_TO_PROCESS,
  REQUESTS_PER_SECOND: CONCURRENT_REQUESTS_PER_WORKER,
  EXTRACTION_SCHEMA,
};
fs.writeFileSync(configFilePath, JSON.stringify(configData, null, 2));

function createCsvWriter(
  model: "HighQuality" | "Fast",
  ocrStrategy: "All" | "Auto" | "Off",
  type: "progress"
) {
  const configFolder = path.join(
    RUN_FOLDER,
    `${model.toLowerCase()}_${ocrStrategy.toLowerCase()}`
  );
  if (!fs.existsSync(configFolder)) {
    fs.mkdirSync(configFolder, { recursive: true });
  }

  const fileName = "task_progress.csv";
  const filePath = path.join(configFolder, fileName);

  const header = [
    { id: "task_id", title: "task_id" },
    { id: "file_name", title: "file_name" },
    { id: "page_count", title: "page_count" },
    { id: "message", title: "message" },
    { id: "start_time", title: "start_time" },
    { id: "end_time", title: "end_time" },
    { id: "duration_ms", title: "duration_ms" },
  ];

  return createObjectCsvWriter({
    path: filePath,
    header: header,
    append: true,
  });
}

async function makeRequest(filePath: string, config: ModelConfig) {
  try {
    const form = new FormData();

    // Add file
    const fileBuffer = fs.readFileSync(filePath);
    form.append("file", fileBuffer, {
      filename: path.basename(filePath),
      contentType: "application/pdf",
    });

    // Add other fields
    form.append("model", config.model);
    form.append("segmentation_strategy", config.segmentationStrategy);
    form.append("target_chunk_length", "512");
    form.append("ocr_strategy", config.ocrStrategy);

    // Create the JSON schema with the correct format
    const schema = {
      title: "Document Metadata",
      type: "object",
      properties: [
        // Note: This should be an array, not an object
        {
          name: "title",
          title: "Document Title",
          type: "string",
          description: "The main title of the document",
          default: null,
        },
        {
          name: "author",
          title: "Author",
          type: "string",
          description: "The author(s) of the document",
          default: null,
        },
        {
          name: "date_published",
          title: "Date Published",
          type: "string",
          description: "The publication date of the document",
          default: null,
        },
        {
          name: "location",
          title: "Location",
          type: "string",
          description: "The location mentioned in the document",
          default: null,
        },
      ],
    };

    // Append the JSON schema with the correct content type
    form.append("json_schema", JSON.stringify(schema), {
      contentType: "application/json",
    });

    try {
      const response = await axios.post<TaskResponse>(API_URL, form, {
        headers: {
          ...form.getHeaders(),
          Authorization: API_KEY,
        },
      });
      return response.data;
    } catch (error: any) {
      if (error.response) {
        console.error("API Error Response:", {
          status: error.response.status,
          data: error.response.data,
        });
      }
      return null;
    }
  } catch (error) {
    console.error("Form creation failed:", error);
    return null;
  }
}

async function pollTask(
  taskId: string,
  config: ModelConfig
): Promise<TaskResponse | null> {
  console.log(
    `Starting task ${taskId} for model ${config.model} with OCR strategy ${config.ocrStrategy}`
  );
  const progressCsvWriter = createCsvWriter(
    config.model,
    config.ocrStrategy,
    "progress"
  );
  let lastMessage = "";
  let messageStartTime = new Date().toISOString();
  let taskStartTime = new Date().toISOString();

  while (true) {
    try {
      const response = await axios.get<TaskResponse>(`${API_URL}/${taskId}`, {
        headers: { Authorization: API_KEY },
      });
      const task = response.data;
      const currentTime = new Date().toISOString();

      if (task.message !== lastMessage) {
        if (lastMessage !== "") {
          const startDate = new Date(messageStartTime);
          const endDate = new Date(currentTime);
          const durationMs = endDate.getTime() - startDate.getTime();

          await progressCsvWriter.writeRecords([
            {
              task_id: task.task_id,
              file_name: task.file_name,
              page_count: task.page_count,
              message: lastMessage,
              start_time: messageStartTime,
              end_time: currentTime,
              duration_ms: durationMs,
            },
          ]);
        }

        lastMessage = task.message;
        messageStartTime = currentTime;
      }

      if (task.status === "Succeeded" && task.output) {
        const configFolder = path.join(
          RUN_FOLDER,
          `${config.model.toLowerCase()}_${config.ocrStrategy.toLowerCase()}`
        );

        // Create outputs subfolder
        const outputsFolder = path.join(configFolder, "json_outputs");
        if (!fs.existsSync(outputsFolder)) {
          fs.mkdirSync(outputsFolder, { recursive: true });
        }

        // Save JSON output with filename as identifier
        const outputFileName = `${task.file_name.replace(/\.[^/.]+$/, "")}_output.json`;
        const outputPath = path.join(outputsFolder, outputFileName);
        fs.writeFileSync(
          outputPath,
          JSON.stringify(
            {
              file_name: task.file_name,
              task_id: task.task_id,
              output: task.output,
            },
            null,
            2
          )
        );
      }

      if (task.status === "Succeeded" || task.status === "Failed") {
        const startDate = new Date(taskStartTime);
        const endDate = new Date(currentTime);
        const durationMs = endDate.getTime() - startDate.getTime();

        await progressCsvWriter.writeRecords([
          {
            task_id: task.task_id,
            file_name: task.file_name,
            page_count: task.page_count,
            message: lastMessage,
            start_time: messageStartTime,
            end_time: currentTime,
            duration_ms: durationMs,
          },
        ]);

        console.log(`Task ${taskId} finished with status: ${task.status}`);
        console.log(`Page count for task ${taskId}: ${task.page_count}`);
        return task;
      }

      await new Promise((resolve) => setTimeout(resolve, 1000));
    } catch (error) {
      console.error(`Error polling task ${taskId}:`, error);
      break;
    }
  }

  return null;
}

function distributeFiles(
  files: string[],
  configs: (ModelConfig & { workers: number })[]
): Map<string, string[]> {
  const distribution = new Map<string, string[]>();
  let fileIndex = 0;

  configs.forEach((config) => {
    const configKey = `${config.model}_${config.ocrStrategy}`;
    const filesToProcess = Math.floor(
      (MAX_FILES_TO_PROCESS * config.percentage) / 100
    );
    distribution.set(configKey, []);

    for (let i = 0; i < filesToProcess && fileIndex < files.length; i++) {
      distribution.get(configKey)!.push(files[fileIndex]);
      fileIndex++;
    }
  });

  return distribution;
}

async function runLoadTest(
  config: ModelConfig,
  assignedFiles: string[]
): Promise<{ totalPages: number; failureTypes: FailureTypes }> {
  let processedFiles = 0;
  let totalPages = 0;
  let failureTypes: FailureTypes = {
    startTaskFailed: 0,
    pollTaskFailed: 0,
    taskStatusFailed: 0,
  };

  const limit = pLimit(CONCURRENT_REQUESTS_PER_WORKER);

  const tasks = assignedFiles.map((file) => {
    return limit(async () => {
      const filePath = path.join(INPUT_FOLDER, file);
      const task = await makeRequest(filePath, config);

      if (task) {
        const pollResult = await pollTask(task.task_id, config);
        if (pollResult) {
          if (pollResult.status === "Succeeded") {
            processedFiles++;
            totalPages += pollResult.page_count;
            console.log(
              `Processed file ${file} with ${pollResult.page_count} pages`
            );
            // Send message to main thread for each processed page
            for (let i = 0; i < pollResult.page_count; i++) {
              parentPort?.postMessage({ type: "pageProcessed" });
            }
          } else if (pollResult.status === "Failed") {
            console.error(
              `Task failed for file ${file}: ${pollResult.message}`
            );
            failureTypes.taskStatusFailed++;
          }
        } else {
          console.error(`Failed to poll task for file ${file}`);
          failureTypes.pollTaskFailed++;
        }
      } else {
        console.error(`Failed to start task for file ${file}`);
        failureTypes.startTaskFailed++;
      }
    });
  });

  await Promise.all(tasks);

  // Write results to a text file
  const resultFilePath = path.join(
    RUN_FOLDER,
    `${config.model}_${config.ocrStrategy}_results.txt`
  );
  const resultContent = `
Total pages processed: ${totalPages}
Failed to start task: ${failureTypes.startTaskFailed}
Failed to poll task: ${failureTypes.pollTaskFailed}
Tasks completed with failure status: ${failureTypes.taskStatusFailed}
Total failed files: ${failureTypes.startTaskFailed + failureTypes.pollTaskFailed + failureTypes.taskStatusFailed}
  `.trim();

  fs.writeFileSync(resultFilePath, resultContent);

  return { totalPages, failureTypes };
}

let runStartTime = 0;
let totalProcessedPages = 0;
const AGGREGATE_LOG_INTERVAL = 1000;
const aggregateLogPath = path.join(RUN_FOLDER, "aggregate_log.csv");

function initializeAggregateLog() {
  runStartTime = performance.now();
  fs.writeFileSync(aggregateLogPath, "Time (s),Pages Processed,Pages/Second\n");
}

function updateAggregateLog() {
  const currentTime = performance.now();
  const elapsedSeconds = (currentTime - runStartTime) / 1000;
  const pagesPerSecond = totalProcessedPages / elapsedSeconds;

  const logEntry = `${elapsedSeconds.toFixed(2)},${totalProcessedPages},${pagesPerSecond.toFixed(2)}\n`;
  fs.appendFileSync(aggregateLogPath, logEntry);
}

function calculateAggregateResults(results: WorkerResult[]): AggregateResults {
  const totalTime =
    Math.max(...results.map((r) => r.endTime)) -
    Math.min(...results.map((r) => r.startTime));
  const totalPages = results.reduce((sum, r) => sum + r.totalPages, 0);
  const pagesPerSecond = totalPages / (totalTime / 1000);

  return {
    totalTime,
    totalPages,
    pagesPerSecond,
  };
}

function updateConfigFile(results: AggregateResults) {
  const configFilePath = path.join(RUN_FOLDER, "config.txt");
  const configData = JSON.parse(fs.readFileSync(configFilePath, "utf-8"));

  configData.aggregateResults = results;

  fs.writeFileSync(configFilePath, JSON.stringify(configData, null, 2));
}

function updateWorkerResultFile(
  config: ModelConfig,
  result: WorkerResult & { failureTypes: FailureTypes },
  workerId: number
) {
  const duration = (result.endTime - result.startTime) / 1000;
  const totalFailedFiles =
    result.failureTypes.startTaskFailed +
    result.failureTypes.pollTaskFailed +
    result.failureTypes.taskStatusFailed;

  // Update only the combined results file
  const combinedFilePath = path.join(
    RUN_FOLDER,
    `${config.model}_${config.ocrStrategy}_combined_results.txt`
  );

  let existingResults = {
    totalPages: 0,
    startTaskFailed: 0,
    pollTaskFailed: 0,
    taskStatusFailed: 0,
  };

  if (fs.existsSync(combinedFilePath)) {
    const content = fs.readFileSync(combinedFilePath, "utf-8");
    const matches = content.match(/Total pages processed: (\d+)/);
    if (matches) {
      existingResults.totalPages = parseInt(matches[1]);
    }
  }

  const combinedPages = existingResults.totalPages + result.totalPages;
  const combinedContent = `
Combined Results:
Total pages processed: ${combinedPages}
Failed to start task: ${existingResults.startTaskFailed + result.failureTypes.startTaskFailed}
Failed to poll task: ${existingResults.pollTaskFailed + result.failureTypes.pollTaskFailed}
Tasks completed with failure status: ${existingResults.taskStatusFailed + result.failureTypes.taskStatusFailed}
Total failed files: ${totalFailedFiles}
  `.trim();

  fs.writeFileSync(combinedFilePath, combinedContent);
}

if (isMainThread) {
  const files = fs.readdirSync(INPUT_FOLDER);
  const fileDistribution = distributeFiles(files, MODEL_CONFIGS);
  const numWorkers = MODEL_CONFIGS.reduce(
    (sum, config) => sum + config.workers,
    0
  );
  console.log(`Starting ${numWorkers} workers...`);
  let completedWorkers = 0;

  const workerResults: WorkerResult[] = [];

  initializeAggregateLog();
  const aggregateLogInterval = setInterval(
    updateAggregateLog,
    AGGREGATE_LOG_INTERVAL
  );

  MODEL_CONFIGS.forEach((config) => {
    const configKey = `${config.model}_${config.ocrStrategy}`;
    const assignedFiles = fileDistribution.get(configKey) || [];
    const filesPerWorker = Math.ceil(assignedFiles.length / config.workers);

    for (let i = 0; i < config.workers; i++) {
      const workerFiles = assignedFiles.slice(
        i * filesPerWorker,
        (i + 1) * filesPerWorker
      );

      const worker = new Worker(__filename, {
        workerData: {
          config,
          assignedFiles: workerFiles,
          RUN_FOLDER,
          workerId: i + 1,
        },
      });

      worker.on("message", (message: { type: string; data: WorkerResult }) => {
        if (message.type === "workerComplete") {
          workerResults.push(message.data);
          updateWorkerResultFile(config, message.data, i + 1);
          completedWorkers++;
          if (completedWorkers === numWorkers) {
            eventEmitter.emit("allWorkersComplete");
          }
        } else if (message.type === "pageProcessed") {
          totalProcessedPages++;
        }
      });

      worker.on("error", (error) => {
        console.error(`Worker error: ${error}`);
      });

      worker.on("exit", (code) => {
        if (code !== 0) {
          console.error(`Worker stopped with exit code ${code}`);
        }
      });
    }
  });

  eventEmitter.on("allWorkersComplete", () => {
    clearInterval(aggregateLogInterval);
    updateAggregateLog();
    const aggregateResults = calculateAggregateResults(workerResults);
    updateConfigFile(aggregateResults);
    console.log("Load test completed for all configurations. Exiting...");
    process.exit(0);
  });
} else {
  const {
    config,
    assignedFiles,
    RUN_FOLDER: workerRunFolder,
    workerId,
  } = workerData;
  RUN_FOLDER = workerRunFolder;
  const startTime = performance.now();
  runLoadTest(config, assignedFiles).then(({ totalPages, failureTypes }) => {
    const endTime = performance.now();
    parentPort?.postMessage({
      type: "workerComplete",
      data: { totalPages, failureTypes, startTime, endTime },
    });
  });
}
