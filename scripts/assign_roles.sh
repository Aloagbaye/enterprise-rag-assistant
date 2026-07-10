$SEARCH_ID = az search service show `
>>   --name srch-secure-rag-dev `
>>   --resource-group rg-secure-rag-dev `
>>   --query id `
>>   -o tsv
>>
>> $USER_ID = az ad signed-in-user show `
>>   --query id `
>>   -o tsv
>>
>> az role assignment create `
>>   --assignee-object-id $USER_ID `
>>   --assignee-principal-type User `
>>   --role "Search Service Contributor" `
>>   --scope $SEARCH_ID
>>
>> az role assignment create `
>>   --assignee-object-id $USER_ID `
>>   --assignee-principal-type User `
>>   --role "Search Index Data Contributor" `
>>   --scope $SEARCH_ID
>>
>> az role assignment create `
>>   --assignee-object-id $USER_ID `
>>   --assignee-principal-type User `
>>   --role "Search Index Data Reader" `
>>   --scope $SEARCH_ID
(.venv) PS C:\Users\aloag\SoelTechnologies\enterprise-rag-assistant> $SEARCH_ID = az search service show `
>>   --name srch-secure-rag-dev `
>>   --resource-group rg-secure-rag-dev `
>>   --query id `
>>   -o tsv
>> 
>> $USER_ID = az ad signed-in-user show `
>>   --query id `
>>   -o tsv
>> 
>> az role assignment create `
>>   --assignee-object-id $USER_ID `
>>   --assignee-principal-type User `
>>   --role "Search Service Contributor" `
>>   --scope $SEARCH_ID
>> 
>> az role assignment create `
>>   --assignee-object-id $USER_ID `
>>   --assignee-principal-type User `
>>   --role "Search Index Data Contributor" `
>>   --scope $SEARCH_ID
>>
>> az role assignment create `
>>   --assignee-object-id $USER_ID `
>>   --assignee-principal-type User `
>>   --role "Search Index Data Reader" `
>>   --scope $SEARCH_ID