#!/usr/bin/python3 -i
#
# Copyright (c) 2015-2023 The Khronos Group Inc.
# Copyright (c) 2015-2023 Valve Corporation
# Copyright (c) 2015-2023 LunarG, Inc.
# Copyright (c) 2015-2023 Google Inc.
# Copyright (c) 2023-2023 RasterGrid Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from generators.generator_utils import (buildListVUID, getVUID, incIndent, decIndent, addIndent)
from generators.vulkan_object import (Handle, Command, Struct, Member, Param)
from generators.base_generator import BaseGenerator

# This class is a container for any source code, data, or other behavior that is necessary to
# customize the generator script for a specific target API variant (e.g. Vulkan SC). As such,
# all of these API-specific interfaces and their use in the generator script are part of the
# contract between this repository and its downstream users. Changing or removing any of these
# interfaces or their use in the generator script will have downstream effects and thus
# should be avoided unless absolutely necessary.
class APISpecific:
    # Returns VUIDs to report when detecting undestroyed objects
    @staticmethod
    def getUndestroyedObjectVUID(targetApiName: str, scope: str) -> str:
        match targetApiName:

            # Vulkan specific undestroyed object VUIDs
            case 'vulkan':
                per_scope = {
                    'instance': 'VUID-vkDestroyInstance-instance-00629',
                    'device': 'VUID-vkDestroyDevice-device-00378'
                }

        return per_scope[scope]


    # Tells whether an object handle type is implicitly destroyed because it does not have
    # destroy APIs or its parent object type does not have destroy APIs
    @staticmethod
    def IsImplicitlyDestroyed(targetApiName: str, handleType: str) -> bool:
        match targetApiName:

            # Vulkan specific implicitly destroyed handle types
            case 'vulkan':
                implicitly_destroyed_set = {
                'VkDisplayKHR',
                'VkDisplayModeKHR'
                }

        return handleType in implicitly_destroyed_set


    # Returns whether allocation callback related VUIDs are enabled
    @staticmethod
    def AreAllocVUIDsEnabled(targetApiName: str) -> bool:
        match targetApiName:

            # Vulkan has allocation callback related VUIDs
            case 'vulkan':
                return True


class ObjectTrackerOutputGenerator(BaseGenerator):
    def __init__(self,
                 valid_usage_file):
        BaseGenerator.__init__(self)
        self.valid_vuids = buildListVUID(valid_usage_file)

        # Commands which are not autogenerated but still intercepted
        self.no_autogen_list = [
            'vkDestroyInstance',
            'vkCreateInstance',
            'vkCreateDevice',
            'vkEnumeratePhysicalDevices',
            'vkGetPhysicalDeviceQueueFamilyProperties',
            'vkGetPhysicalDeviceQueueFamilyProperties2',
            'vkGetPhysicalDeviceQueueFamilyProperties2KHR',
            'vkGetDeviceQueue',
            'vkGetDeviceQueue2',
            'vkCreateDescriptorSetLayout',
            'vkDestroyDescriptorPool',
            'vkDestroyCommandPool',
            'vkAllocateCommandBuffers',
            'vkAllocateDescriptorSets',
            'vkFreeDescriptorSets',
            'vkFreeCommandBuffers',
            'vkUpdateDescriptorSets',
            'vkBeginCommandBuffer',
            'vkGetDescriptorSetLayoutSupport',
            'vkGetDescriptorSetLayoutSupportKHR',
            'vkDestroySwapchainKHR',
            'vkGetSwapchainImagesKHR',
            'vkCmdPushDescriptorSetKHR',
            'vkDestroyDevice',
            'vkResetDescriptorPool',
            'vkGetPhysicalDeviceDisplayPropertiesKHR',
            'vkGetPhysicalDeviceDisplayProperties2KHR',
            'vkGetDisplayModePropertiesKHR',
            'vkGetDisplayModeProperties2KHR',
            'vkCreateFramebuffer',
            'vkSetDebugUtilsObjectNameEXT',
            'vkSetDebugUtilsObjectTagEXT',
            'vkCreateDescriptorUpdateTemplate',
            'vkCreateDescriptorUpdateTemplateKHR',
            'vkCmdBuildAccelerationStructuresKHR',
            'vkCmdBuildAccelerationStructuresIndirectKHR',
            'vkBuildAccelerationStructuresKHR',
            'vkCreateRayTracingPipelinesKHR',
            'vkExportMetalObjectsEXT',
            'vkGetDescriptorEXT',
            ]
        # These VUIDS are not implicit, but are best handled in this layer. Codegen for vkDestroy calls will generate a key
        # which is translated here into a good VU.  Saves ~40 checks.
        self.manual_vuids = dict()
        self.manual_vuids = {
            "fence-compatalloc": "\"VUID-vkDestroyFence-fence-01121\"",
            "fence-nullalloc": "\"VUID-vkDestroyFence-fence-01122\"",
            "event-compatalloc": "\"VUID-vkDestroyEvent-event-01146\"",
            "event-nullalloc": "\"VUID-vkDestroyEvent-event-01147\"",
            "buffer-compatalloc": "\"VUID-vkDestroyBuffer-buffer-00923\"",
            "buffer-nullalloc": "\"VUID-vkDestroyBuffer-buffer-00924\"",
            "image-compatalloc": "\"VUID-vkDestroyImage-image-01001\"",
            "image-nullalloc": "\"VUID-vkDestroyImage-image-01002\"",
            "shaderModule-compatalloc": "\"VUID-vkDestroyShaderModule-shaderModule-01092\"",
            "shaderModule-nullalloc": "\"VUID-vkDestroyShaderModule-shaderModule-01093\"",
            "pipeline-compatalloc": "\"VUID-vkDestroyPipeline-pipeline-00766\"",
            "pipeline-nullalloc": "\"VUID-vkDestroyPipeline-pipeline-00767\"",
            "sampler-compatalloc": "\"VUID-vkDestroySampler-sampler-01083\"",
            "sampler-nullalloc": "\"VUID-vkDestroySampler-sampler-01084\"",
            "renderPass-compatalloc": "\"VUID-vkDestroyRenderPass-renderPass-00874\"",
            "renderPass-nullalloc": "\"VUID-vkDestroyRenderPass-renderPass-00875\"",
            "descriptorUpdateTemplate-compatalloc": "\"VUID-vkDestroyDescriptorUpdateTemplate-descriptorSetLayout-00356\"",
            "descriptorUpdateTemplate-nullalloc": "\"VUID-vkDestroyDescriptorUpdateTemplate-descriptorSetLayout-00357\"",
            "imageView-compatalloc": "\"VUID-vkDestroyImageView-imageView-01027\"",
            "imageView-nullalloc": "\"VUID-vkDestroyImageView-imageView-01028\"",
            "pipelineCache-compatalloc": "\"VUID-vkDestroyPipelineCache-pipelineCache-00771\"",
            "pipelineCache-nullalloc": "\"VUID-vkDestroyPipelineCache-pipelineCache-00772\"",
            "pipelineLayout-compatalloc": "\"VUID-vkDestroyPipelineLayout-pipelineLayout-00299\"",
            "pipelineLayout-nullalloc": "\"VUID-vkDestroyPipelineLayout-pipelineLayout-00300\"",
            "descriptorSetLayout-compatalloc": "\"VUID-vkDestroyDescriptorSetLayout-descriptorSetLayout-00284\"",
            "descriptorSetLayout-nullalloc": "\"VUID-vkDestroyDescriptorSetLayout-descriptorSetLayout-00285\"",
            "semaphore-compatalloc": "\"VUID-vkDestroySemaphore-semaphore-01138\"",
            "semaphore-nullalloc": "\"VUID-vkDestroySemaphore-semaphore-01139\"",
            "queryPool-compatalloc": "\"VUID-vkDestroyQueryPool-queryPool-00794\"",
            "queryPool-nullalloc": "\"VUID-vkDestroyQueryPool-queryPool-00795\"",
            "bufferView-compatalloc": "\"VUID-vkDestroyBufferView-bufferView-00937\"",
            "bufferView-nullalloc": "\"VUID-vkDestroyBufferView-bufferView-00938\"",
            "surface-compatalloc": "\"VUID-vkDestroySurfaceKHR-surface-01267\"",
            "surface-nullalloc": "\"VUID-vkDestroySurfaceKHR-surface-01268\"",
            "framebuffer-compatalloc": "\"VUID-vkDestroyFramebuffer-framebuffer-00893\"",
            "framebuffer-nullalloc": "\"VUID-vkDestroyFramebuffer-framebuffer-00894\"",
            "VkGraphicsPipelineCreateInfo-basePipelineHandle": "\"VUID-VkGraphicsPipelineCreateInfo-flags-07984\"",
            "VkComputePipelineCreateInfo-basePipelineHandle": "\"VUID-VkComputePipelineCreateInfo-flags-07984\"",
            "VkRayTracingPipelineCreateInfoNV-basePipelineHandle": "\"VUID-VkRayTracingPipelineCreateInfoNV-flags-07984\"",
			"VkRayTracingPipelineCreateInfoKHR-basePipelineHandle": "\"VUID-VkRayTracingPipelineCreateInfoKHR-flags-07984\"",
            "VkVideoSessionKHR-videoSession-compatalloc": "\"VUID-vkDestroyVideoSessionKHR-videoSession-07193\"",
            "VkVideoSessionKHR-videoSession-nullalloc": "\"VUID-vkDestroyVideoSessionKHR-videoSession-07194\"",
            "VkVideoSessionParametersKHR-videoSessionParameters-compatalloc": "\"VUID-vkDestroyVideoSessionParametersKHR-videoSessionParameters-07213\"",
            "VkVideoSessionParametersKHR-videoSessionParameters-nullalloc": "\"VUID-vkDestroyVideoSessionParametersKHR-videoSessionParameters-07214\"",
            "VkAccelerationStructureKHR-accelerationStructure-compatalloc": "\"VUID-vkDestroyAccelerationStructureKHR-accelerationStructure-02443\"",
            "VkAccelerationStructureKHR-accelerationStructure-nullalloc": "\"VUID-vkDestroyAccelerationStructureKHR-accelerationStructure-02444\"",
            "VkAccelerationStructureNV-accelerationStructure-compatalloc": "\"VUID-vkDestroyAccelerationStructureNV-accelerationStructure-03753\"",
            "VkAccelerationStructureNV-accelerationStructure-nullalloc": "\"VUID-vkDestroyAccelerationStructureNV-accelerationStructure-03754\"",
            "shader-compatalloc": "\"VUID-vkDestroyShaderEXT-pAllocator-08483\"",
            "shader-nullalloc": "\"VUID-vkDestroyShaderEXT-pAllocator-08484\"",
           }

    # Work up Handle's parents to see if it VkDevice
    def isParentDevice(self, handle: Handle) -> bool:
        while handle.parent is not None:
            if handle.parent.name == 'VkDevice':
                return True
            handle = handle.parent
        return False

    def generate(self):
        self.write(f'''// *** THIS FILE IS GENERATED - DO NOT EDIT ***
// See {os.path.basename(__file__)} for modifications

/***************************************************************************
*
* Copyright (c) 2015-2023 The Khronos Group Inc.
* Copyright (c) 2015-2023 Valve Corporation
* Copyright (c) 2015-2023 LunarG, Inc.
* Copyright (c) 2015-2023 Google Inc.
* Copyright (c) 2015-2023 RasterGrid Kft.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
****************************************************************************/\n''')
        self.write('// NOLINTBEGIN') # Wrap for clang-tidy to ignore

        if self.filename == 'object_tracker.h':
            self.generateHeader()
        elif self.filename == 'object_tracker.cpp':
            self.generateSource()
        else:
            self.write(f'\nFile name {self.filename} has no code to generate\n')

        self.write('// NOLINTEND') # Wrap for clang-tidy to ignore


    def generateHeader(self):
        out = []
        for command in self.vk.commands.values():
            out.extend([f'#ifdef {command.protect}\n'] if command.protect else [])
            (pre_call_validate, pre_call_record, post_call_record) = self.generateFunctionBody(command)

            prototype = (command.cPrototype.split('VKAPI_CALL ')[1])[2:-1]
            terminator = ';\n' if 'ValidationCache' in command.name else ' override;\n'

            if pre_call_validate:
                prePrototype = prototype.replace(')', ',\n    const ErrorObject&                          error_obj)')
                out.append(f'bool PreCallValidate{prePrototype} const{terminator}')

            if pre_call_record:
                out.append(f'void PreCallRecord{prototype}{terminator}')

            if post_call_record:
                prototype = prototype.replace(')', ',\n    const RecordObject&                         record_obj)')
                out.append(f'void PostCallRecord{prototype}{terminator}')

            out.extend([f'#endif // {command.protect}\n'] if command.protect else [])

        out.append('''

void PostCallRecordDestroyInstance(VkInstance instance, const VkAllocationCallbacks *pAllocator, const RecordObject& record_obj) override;
void PreCallRecordResetDescriptorPool(VkDevice device, VkDescriptorPool descriptorPool, VkDescriptorPoolResetFlags flags) override;
void PostCallRecordGetPhysicalDeviceQueueFamilyProperties(VkPhysicalDevice physicalDevice, uint32_t *pQueueFamilyPropertyCount, VkQueueFamilyProperties *pQueueFamilyProperties, const RecordObject& record_obj) override;
void PreCallRecordFreeCommandBuffers(VkDevice device, VkCommandPool commandPool, uint32_t commandBufferCount, const VkCommandBuffer *pCommandBuffers) override;
void PreCallRecordFreeDescriptorSets(VkDevice device, VkDescriptorPool descriptorPool, uint32_t descriptorSetCount, const VkDescriptorSet *pDescriptorSets) override;
void PostCallRecordGetPhysicalDeviceQueueFamilyProperties2(VkPhysicalDevice physicalDevice, uint32_t *pQueueFamilyPropertyCount, VkQueueFamilyProperties2 *pQueueFamilyProperties, const RecordObject& record_obj) override;
void PostCallRecordGetPhysicalDeviceQueueFamilyProperties2KHR(VkPhysicalDevice physicalDevice, uint32_t *pQueueFamilyPropertyCount, VkQueueFamilyProperties2 *pQueueFamilyProperties, const RecordObject& record_obj) override;
void PostCallRecordGetPhysicalDeviceDisplayPropertiesKHR(VkPhysicalDevice physicalDevice, uint32_t *pPropertyCount, VkDisplayPropertiesKHR *pProperties, const RecordObject& record_obj) override;
void PostCallRecordGetDisplayModePropertiesKHR(VkPhysicalDevice physicalDevice, VkDisplayKHR display, uint32_t *pPropertyCount, VkDisplayModePropertiesKHR *pProperties, const RecordObject& record_obj) override;
void PostCallRecordGetPhysicalDeviceDisplayProperties2KHR(VkPhysicalDevice physicalDevice, uint32_t *pPropertyCount, VkDisplayProperties2KHR *pProperties, const RecordObject& record_obj) override;
void PostCallRecordGetDisplayModeProperties2KHR(VkPhysicalDevice physicalDevice, VkDisplayKHR display, uint32_t *pPropertyCount, VkDisplayModeProperties2KHR *pProperties, const RecordObject& record_obj) override;
void PostCallRecordGetPhysicalDeviceDisplayPlanePropertiesKHR(VkPhysicalDevice physicalDevice, uint32_t* pPropertyCount, VkDisplayPlanePropertiesKHR* pProperties, const RecordObject& record_obj) override;
void PostCallRecordGetPhysicalDeviceDisplayPlaneProperties2KHR(VkPhysicalDevice physicalDevice, uint32_t* pPropertyCount, VkDisplayPlaneProperties2KHR* pProperties, const RecordObject& record_obj) override;
''')
        self.write("".join(out))

    def generateSource(self):
        out = []
        out.append('''
#include "chassis.h"
#include "object_tracker/object_lifetime_validation.h"
ReadLockGuard ObjectLifetimes::ReadLock() const { return ReadLockGuard(validation_object_mutex, std::defer_lock); }
WriteLockGuard ObjectLifetimes::WriteLock() { return WriteLockGuard(validation_object_mutex, std::defer_lock); }

// ObjectTracker undestroyed objects validation function
bool ObjectLifetimes::ReportUndestroyedInstanceObjects(VkInstance instance, const Location& loc) const {
    bool skip = false;
    const std::string error_code = "%s";
''' % APISpecific.getUndestroyedObjectVUID(self.targetApiName, 'instance'))
        for handle in [x for x in self.vk.handles.values() if not x.dispatchable and not self.isParentDevice(x)]:
            comment_prefix = ''
            if APISpecific.IsImplicitlyDestroyed(self.targetApiName, handle.name):
                comment_prefix = '// No destroy API or implicitly freed/destroyed -- do not report: '
            out.append(f'    {comment_prefix}skip |= ReportLeakedInstanceObjects(instance, kVulkanObjectType{handle.name[2:]}, error_code, loc);\n')
        out.append('    return skip;\n')
        out.append('}\n')

        out.append('''
bool ObjectLifetimes::ReportUndestroyedDeviceObjects(VkDevice device, const Location& loc) const {
    bool skip = false;
    const std::string error_code = "%s";
''' % APISpecific.getUndestroyedObjectVUID(self.targetApiName, 'device'))

        comment_prefix = ''
        if APISpecific.IsImplicitlyDestroyed(self.targetApiName, 'VkCommandBuffer'):
            comment_prefix = '// No destroy API or implicitly freed/destroyed -- do not report: '
        out.append(f'    {comment_prefix}skip |= ReportLeakedDeviceObjects(device, kVulkanObjectTypeCommandBuffer, error_code, loc);\n')

        for handle in [x for x in self.vk.handles.values() if not x.dispatchable and self.isParentDevice(x)]:
            comment_prefix = ''
            if APISpecific.IsImplicitlyDestroyed(self.targetApiName, handle.name):
                comment_prefix = '// No destroy API or implicitly freed/destroyed -- do not report: '
            out.append(f'    {comment_prefix}skip |= ReportLeakedDeviceObjects(device, kVulkanObjectType{handle.name[2:]}, error_code, loc);\n')
        out.append('    return skip;\n')
        out.append('}\n')

        out.append('\nvoid ObjectLifetimes::DestroyLeakedInstanceObjects() {\n')
        for handle in [x for x in self.vk.handles.values() if not x.dispatchable and not self.isParentDevice(x)]:
            out.append(f'    DestroyUndestroyedObjects(kVulkanObjectType{handle.name[2:]});\n')
        out.append('}\n')

        out.append('\nvoid ObjectLifetimes::DestroyLeakedDeviceObjects() {\n')
        out.append('    DestroyUndestroyedObjects(kVulkanObjectTypeCommandBuffer);\n')
        for handle in [x for x in self.vk.handles.values() if not x.dispatchable and self.isParentDevice(x)]:
            out.append(f'    DestroyUndestroyedObjects(kVulkanObjectType{handle.name[2:]});\n')
        out.append('}\n')

        for command in [x for x in self.vk.commands.values() if x.name not in self.no_autogen_list]:
            out.extend([f'#ifdef {command.protect}\n'] if command.protect else [])

            # Generate object handling code
            (pre_call_validate, pre_call_record, post_call_record) = self.generateFunctionBody(command)

            prototype = (command.cPrototype.split('VKAPI_CALL ')[1])[2:-1]

            # Output PreCallValidateAPI function if necessary
            if pre_call_validate:
                prePrototype = prototype.replace(')', ',\n    const ErrorObject&                          error_obj)')
                out.append('\n')
                out.append(f'bool ObjectLifetimes::PreCallValidate{prePrototype} const {{\n')
                out.append('    bool skip = false;\n')
                out.append(f'{pre_call_validate}\n')
                out.append('    return skip;\n')
                out.append('}\n')

            # Output PreCallRecordAPI function if necessary
            if pre_call_record:
                out.append('\n')
                out.append(f'void ObjectLifetimes::PreCallRecord{prototype} {{\n')
                out.append(f'{pre_call_record}\n')
                out.append('}\n')

            # Output PosCallRecordAPI function if necessary
            if post_call_record:
                out.append('\n')
                postPrototype = f'void ObjectLifetimes::PostCallRecord{prototype} {{\n'
                postPrototype = postPrototype.replace(')', ',\n    const RecordObject&                         record_obj)')
                if command.returnType == 'VkResult':
                    failureCondition = 'record_obj.result != VK_SUCCESS'
                    # VK_INCOMPLETE is considered a success
                    if 'EnumeratePhysicalDeviceGroups' in command.name:
                        failureCondition += ' && record_obj.result != VK_INCOMPLETE'
                    if 'CreateShadersEXT' in command.name:
                        failureCondition += ' && record_obj.result != VK_ERROR_INCOMPATIBLE_SHADER_BINARY_EXT'
                    # The two createpipelines APIs may create on failure -- skip the success result check
                    if 'CreateGraphicsPipelines' not in command.name and 'CreateComputePipelines' not in command.name and 'CreateRayTracingPipelines' not in command.name:
                        postPrototype = postPrototype.replace('{', f'{{\n    if ({failureCondition}) return;')
                out.append(postPrototype)

                out.append(f'{post_call_record}\n')
                out.append('}\n')

            out.extend([f'#endif // {command.protect}\n'] if command.protect else [])

        self.write("".join(out))

    def structContainsObject(self, struct: Struct) -> bool:
        for member in struct.members:
            if member.type in self.vk.handles:
                return True
            # recurse for member structs, guard against infinite recursion
            elif member.type in self.vk.structs and member.type != struct.name:
                if self.structContainsObject(self.vk.structs[member.type]):
                    return True
        return False

    def getAllocVUID(self, param: Param, allocType: str) -> str:
        # Do not report allocation callback VUIDs if the target API does not support them
        if not APISpecific.AreAllocVUIDsEnabled(self.targetApiName):
            return "kVUIDUndefined"

        lookup_string = '%s-%s' %(param.name, allocType)
        vuid = self.manual_vuids.get(lookup_string, None)
        if vuid is not None:
            return vuid
        lookup_string = '%s-%s-%s' %(param.type, param.name, allocType)
        vuid = self.manual_vuids.get(lookup_string, None)
        if vuid is not None:
            return vuid
        return "kVUIDUndefined"

    # recursively walks struct members (and command params)
    # parentName == Struct or Command calling into this
    # topCommand == The command called from (when in a struct)
    def validateObjects(self, members: list[Member], indent: str, prefix: str, arrayIndex: int, parentName: str, topCommand: str, errorLoc: str, isTopLevelCreate: bool) -> str:
        pre_call_validate = ''
        index = f'index{str(arrayIndex)}'
        arrayIndex += 1
        # Process any objects in this structure and recurse for any sub-structs in this struct
        for member in members:
            if isTopLevelCreate and member == members[-1]:
                continue # ignore last param of creation commands

            if member.type in self.vk.handles:
                if member.noAutoValidity:
                    nullAllowed = 'true'
                elif member.length:
                    nullAllowed = str(member.optionalPointer).lower()
                else:
                    nullAllowed = str(member.optional).lower()

                # Replace with alias if one
                alias = self.vk.commands[parentName].alias if parentName in self.vk.commands else None
                parent = alias if alias else parentName
                vuid_string = f'VUID-{parent}-{member.name}-parameter'
                # TODO: Currently just brute force check all VUs, but shuold be smarter what makes these `-parameter` VUs
                paramVUID = f'"{vuid_string}"' if vuid_string in self.valid_vuids else "kVUIDUndefined"

                # TODO: Revise object 'parent' handling.  Each object definition in the XML specifies a parent, this should
                #       all be handled in codegen (or at least called out)
                # These objects do not have a VkDevice as their (ultimate) parent objecs, so skip the current code-gen'd parent checks
                parentVUID = 'kVUIDUndefined'
                parent_exception_list = [
                    'VkPhysicalDevice',
                    'VkSwapchainKHR',
                    'VkDisplayKHR',
                    'VkSurfaceKHR',
                    'VkDisplayModeKHR',
                    'VkDebugReportCallbackEXT',
                    'VkDebugUtilsMessengerEXT']
                # always skip the first member, its the dispatch handle and has not parent VUs
                if member.type not in parent_exception_list and member != members[0]:
                    # Replace with alias if one
                    alias = self.vk.commands[parentName].alias if parentName in self.vk.commands else None
                    parent = alias if alias else parentName

                    if members[0].type == 'VkDevice':
                        parentVUID = getVUID(self.valid_vuids, f'VUID-{parent}-{member.name}-parent')
                    # Can only have a 'common parent' VU if there are 2 handles and one isn't a VkDevice
                    elif len([x for x in members if x.type in self.vk.handles]) > 1:
                        parentVUID = getVUID(self.valid_vuids, f'VUID-{parent}-commonparent')
                    elif topCommand != parentName: # in a struct
                        # TODO: https://gitlab.khronos.org/vulkan/vulkan/-/issues/3553#note_424431
                        # There are many cases where the handle in the struct needs to be the same device as
                        # the calling function, but currently no VUs are generated from the spec
                        #
                        # Adding this one vkCreateImageView as has been seen in real world and a VU was created already
                        if topCommand == 'vkCreateImageView' and member.name == 'image':
                            parentVUID = "\"VUID-vkCreateImageView-image-09179\""

                if member.length:
                    location = f'{errorLoc}.dot(Field::{member.name}, {index})'
                    countName = f'{prefix}{member.length}'
                    pre_call_validate += addIndent(indent,
f'''if (({countName} > 0) && ({prefix}{member.name})) {{
    for (uint32_t {index} = 0; {index} < {countName}; ++{index}) {{
        skip |= ValidateObject({prefix}{member.name}[{index}], kVulkanObjectType{member.type[2:]}, {nullAllowed}, {paramVUID}, {parentVUID}, {location});
    }}
}}''')
                elif 'basePipelineHandle' in member.name:
                    pre_call_validate += f'{indent}if (({prefix}flags & VK_PIPELINE_CREATE_DERIVATIVE_BIT) && ({prefix}basePipelineIndex == -1))\n'
                    manual_vuid_index = parentName + '-' + member.name
                    paramVUID = self.manual_vuids.get(manual_vuid_index, "kVUIDUndefined")
                    pre_call_validate += f'{indent}    skip |= ValidateObject({prefix}{member.name}, kVulkanObjectType{member.type[2:]}, false, {paramVUID}, {parentVUID}, error_obj.location);\n'
                else:
                    location = f'{errorLoc}.dot(Field::{member.name})'
                    pre_call_validate += f'{indent}skip |= ValidateObject({prefix}{member.name}, kVulkanObjectType{member.type[2:]}, {nullAllowed}, {paramVUID}, {parentVUID}, {location});\n'

            # Handle Structs that contain objects at some level
            elif member.type in self.vk.structs:
                struct = self.vk.structs[member.type]
                # Structs at first level will have an object
                if self.structContainsObject(struct):
                    # Struct Array
                    if member.length is not None:
                        # Update struct prefix
                        pre_call_validate += f'{indent}if ({prefix}{member.name}) {{\n'
                        indent = incIndent(indent)
                        pre_call_validate += f'{indent}for (uint32_t {index} = 0; {index} < {prefix}{member.length}; ++{index}) {{\n'
                        indent = incIndent(indent)
                        new_error_loc = f'{index}_loc'
                        pre_call_validate += f'{indent}const Location {new_error_loc} = {errorLoc}.dot(Field::{member.name}, {index});\n'
                        new_prefix = f'{prefix}{member.name}[{index}].'
                        # Process sub-structs in this struct
                        pre_call_validate += self.validateObjects(struct.members, indent, new_prefix, arrayIndex, member.type, topCommand, new_error_loc, False)
                        indent = decIndent(indent)
                        pre_call_validate += f'{indent}}}\n'
                        indent = decIndent(indent)
                        pre_call_validate += f'{indent}}}\n'
                    # Single Struct Pointer
                    elif member.pointer:
                        # Update struct prefix
                        new_prefix = f'{prefix}{member.name}->'
                        # Declare safe_VarType for struct
                        pre_call_validate += f'{indent}if ({prefix}{member.name}) {{\n'
                        indent = incIndent(indent)
                        new_error_loc = f'{member.name}_loc'
                        pre_call_validate += f'{indent}const Location {new_error_loc} = {errorLoc}.dot(Field::{member.name});\n'
                        # Process sub-structs in this struct
                        pre_call_validate += self.validateObjects(struct.members, indent, new_prefix, arrayIndex, member.type, topCommand, new_error_loc, False)
                        indent = decIndent(indent)
                        pre_call_validate += '%s}\n' % indent
                    # Single Nested Struct
                    else:
                        # Update struct prefix
                        new_prefix = f'{prefix}{member.name}.'
                        new_error_loc = f'{member.name}_loc'
                        pre_call_validate += f'{indent}const Location {new_error_loc} = {errorLoc}.dot(Field::{member.name});\n'
                        # Process sub-structs
                        pre_call_validate += self.validateObjects(struct.members, indent, new_prefix, arrayIndex, member.type, topCommand, new_error_loc, False)
        return pre_call_validate
    #
    # For a particular API, generate the object handling code
    def generateFunctionBody(self, command: Command):
        indent = '    '
        pre_call_validate = ''
        pre_call_record = ''
        post_call_record = ''

        isCreate = any(x in command.name for x in ['Create', 'Allocate', 'Enumerate', 'RegisterDeviceEvent', 'RegisterDisplayEvent', 'AcquirePerformanceConfigurationINTEL']) or ('vkGet' in command.name and command.params[-1].pointer)
        isDestroy = any(x in command.name for x in ['Destroy', 'Free', 'ReleasePerformanceConfigurationINTEL'])

        pre_call_validate += self.validateObjects(command.params, indent, '', 0, command.name, command.name, 'error_obj.location', isCreate)

        # Handle object create operations if last parameter is created by this call
        if isCreate:
            handle_type = command.params[-1].type
            isCreatePipelines = 'CreateGraphicsPipelines' in command.name or 'CreateComputePipelines' in command.name or 'CreateRayTracingPipelines' in command.name
            isCreateShaders = 'CreateShaders' in command.name

            if handle_type in self.vk.handles:
                # Check for special case where multiple handles are returned
                objectArray = command.params[-1].length is not None

                if objectArray:
                    if isCreatePipelines:
                        post_call_record += f'{indent}if (VK_ERROR_VALIDATION_FAILED_EXT == record_obj.result) return;\n'

                    post_call_record += f'{indent}if ({command.params[-1].name}) {{\n'
                    indent = incIndent(indent)
                    countIsPointer = '*' if command.params[-2].type == 'uint32_t' and command.params[-2].pointer else ''
                    post_call_record += f'{indent}for (uint32_t index = 0; index < {countIsPointer}{command.params[-1].length}; index++) {{\n'
                    indent = incIndent(indent)

                if isCreatePipelines:
                    post_call_record += f'{indent}if (!pPipelines[index]) continue;\n'
                elif isCreateShaders:
                    post_call_record += f'{indent}if (!pShaders[index]) break;\n'

                allocator = command.params[-2].name if command.params[-2].type == 'VkAllocationCallbacks' else 'nullptr'
                objectDest = f'{command.params[-1].name}[index]' if objectArray else f'*{command.params[-1].name}'
                post_call_record += f'{indent}CreateObject({objectDest}, kVulkanObjectType{handle_type[2:]}, {allocator});\n'
                if objectArray:
                    indent = decIndent(indent)
                    post_call_record += f'{indent}}}\n'
                    indent = decIndent(indent)
                    post_call_record += f'{indent}}}\n'
            # Physical device groups are not handles, but a set of handles, they need to be tracked as well
            elif handle_type == 'VkPhysicalDeviceGroupProperties':
                post_call_record += f'''{indent}if ({command.params[-1].name}) {{
{indent}{indent}const RecordObject record_obj(vvl::Func::vkEnumeratePhysicalDevices, VK_SUCCESS);
{indent}{indent}for (uint32_t device_group_index = 0; device_group_index < *{command.params[-2].name}; device_group_index++) {{
{indent}{indent}{indent}PostCallRecordEnumeratePhysicalDevices({command.params[0].name}, &{command.params[-1].name}[device_group_index].physicalDeviceCount, {command.params[-1].name}[device_group_index].physicalDevices, record_obj);
{indent}{indent}}}
{indent}}}\n'''
        # Handle object destroy operations
        if isDestroy:
            # Check for special case where multiple handles are returned
            handle_param = command.params[-1] if 'ReleasePerformanceConfigurationINTEL' in command.name else command.params[-2]
            allocator = 'nullptr' if 'ReleasePerformanceConfigurationINTEL' in command.name else 'pAllocator'

            compatallocVUID = self.getAllocVUID(handle_param, "compatalloc")
            nullallocVUID = self.getAllocVUID(handle_param, "nullalloc")
            if handle_param.type in self.vk.handles:
                # Call Destroy a single time
                pre_call_validate += f'{indent}skip |= ValidateDestroyObject({handle_param.name}, kVulkanObjectType{handle_param.type[2:]}, {allocator}, {compatallocVUID}, {nullallocVUID}, error_obj.location);\n'
                pre_call_record += f'{indent}RecordDestroyObject({handle_param.name}, kVulkanObjectType{handle_param.type[2:]});\n'

        return pre_call_validate, pre_call_record, post_call_record

