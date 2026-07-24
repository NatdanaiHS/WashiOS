#pragma once

#include <cstdint>

#include "FreeRTOS.h"
#include "task.h"

namespace rtos_config
{

/**
 * @brief Static-allocation base class for WashiOS RTOS tasks.
 *
 * The WashiTask template owns the FreeRTOS task control block and stack storage
 * required to create a task without dynamic memory allocation.
 *
 * @tparam StackDepth Number of StackType_t entries reserved for the task stack.
 */
template<uint32_t StackDepth>
class WashiTask
{
public:
    /**
     * @brief Construct a task object with no active FreeRTOS task handle.
     */
    WashiTask() : xTaskBuffer(), xStack(), taskHandle(nullptr)
    {
    }

    /**
     * @brief Default virtual destructor for safe destruction through base pointers.
     */
    virtual ~WashiTask() = default;

    /**
     * @brief Start the task using statically allocated FreeRTOS memory.
     *
     * @param pcName Pointer to a null-terminated task name string.
     * @param uxPriority FreeRTOS task priority.
     *
     * @return true if the task was created successfully; false otherwise.
     */
    bool Start(const char* pcName, UBaseType_t uxPriority)
    {
        taskHandle = xTaskCreateStatic(&WashiTask::TaskRoutine,
                                       pcName,
                                       StackDepth,
                                       this,
                                       uxPriority,
                                       xStack,
                                       &xTaskBuffer);

        return (taskHandle != nullptr);
    }

protected:
    /**
     * @brief Execute the task body.
     *
     * Derived classes shall implement this method as the task's main execution
     * loop. The method is not expected to return during nominal operation.
     */
    virtual void Run() = 0;

private:
    StaticTask_t xTaskBuffer;
    StackType_t xStack[StackDepth];
    TaskHandle_t taskHandle;

    /**
     * @brief FreeRTOS-compatible task entry point.
     *
     * @param pvParameters Pointer to the WashiTask instance.
     */
    static void TaskRoutine(void* pvParameters)
    {
        WashiTask* const task = static_cast<WashiTask*>(pvParameters);

        if (task != nullptr)
        {
            task->Run();
        }

        vTaskDelete(nullptr);
    }
};

} /* namespace rtos_config */
