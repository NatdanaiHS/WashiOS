#pragma once

#include "ITiming.hpp"
#include "TaskHealth.hpp"

namespace core
{

template<std::size_t RegistryCapacity = 8U>
class TaskHealthReporter
{
public:
    void configure(TaskHealthRegistry<RegistryCapacity>* taskRegistry,
                   hal::ITiming* timingSource,
                   TaskId id)
    {
        registry = taskRegistry;
        timing = timingSource;
        taskId = id;
    }

    bool checkIn()
    {
        return registry != nullptr && timing != nullptr &&
               registry->checkIn(taskId, timing->getSystemTick());
    }

private:
    TaskHealthRegistry<RegistryCapacity>* registry = nullptr;
    hal::ITiming* timing = nullptr;
    TaskId taskId = 0U;
};

} /* namespace core */
